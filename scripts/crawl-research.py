"""Small public-source scanner. No login, private data or arbitrary URLs."""
import argparse
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

AGENT = 'TarkaResearch/1.0 (+https://github.com/AhmedMasum2000000/tarka-collective-preview)'
SITES = [('Social Square','https://socialsquare.co/'),('Bengal Reach','https://www.bengalreach.com/'),('Maroon Ltd.','https://www.maroonltd.com/'),('Ngital','https://ngital.com/')]
TOPICS = [('creator','"Bangladesh" ("influencer" OR "creator marketing" OR "digital marketing")'),('clothing','"Bangladesh" ("fashion" OR "retail" OR "clothing")'),('games','("retro gaming" OR "physical games" OR "game discs")'),('agriculture','"Bangladesh" ("agriculture" OR "fisheries")')]
INDICATORS = [('IT.NET.USER.ZS','Internet use','% of population'),('SP.POP.TOTL','Population','people'),('FP.CPI.TOTL.ZG','Inflation','% annual')]
SERVICES = [('Creator campaigns',r'influencer|creator marketing'),('UGC',r'\bugc\b|user.generated content'),('Video production',r'video production|cinematograph'),('Paid advertising',r'paid ads|paid media|media buying'),('Brand strategy',r'brand strategy|branding'),('Social media management',r'social media management')]

def stamp():
    return datetime.now(timezone.utc).isoformat()

def clean(value, limit=25):
    value = re.sub(r'<[^>]+>',' ',value or '')
    return ' '.join(html.unescape(value).split()[:limit])

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        before = urllib.parse.urlparse(req.full_url)
        after = urllib.parse.urlparse(newurl)
        if after.scheme != 'https' or after.hostname.removeprefix('www.') != before.hostname.removeprefix('www.'):
            raise ValueError('Redirect outside the source domain')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':AGENT,'Accept':'text/html,application/json,application/rss+xml,text/plain'})
    with urllib.request.build_opener(SafeRedirect()).open(request,timeout=18) as response:
        body=response.read(2_000_001)
        if len(body)>2_000_000:
            raise ValueError('Source exceeds the scan size limit')
        return body.decode(response.headers.get_content_charset() or 'utf-8',errors='replace')

def robots_allow(url, getter=fetch):
    robots=urllib.parse.urljoin(url,'/robots.txt')
    try:
        text=getter(robots)
    except urllib.error.HTTPError as error:
        if error.code==404:
            return True
        raise ValueError('Robots policy unavailable') from error
    parser=urllib.robotparser.RobotFileParser(robots)
    parser.parse(text.splitlines())
    return parser.can_fetch(AGENT,url)

def page_details(text):
    title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
    description=''
    for meta in re.findall(r'<meta\b[^>]*>',text,re.I):
        attrs=dict((key.lower(),html.unescape(value)) for key,_,value in re.findall(r'([\w:-]+)\s*=\s*([\'\"])(.*?)\2',meta,re.S))
        if attrs.get('name','').lower()=='description':
            description=attrs.get('content',''); break
    plain=clean(re.sub(r'<(script|style)\b[^>]*>.*?</\1>',' ',text,flags=re.I|re.S),limit=100000).lower()
    return {'title':clean(title.group(1) if title else '',8),'description':clean(description,17),'mentions':[name for name,pattern in SERVICES if re.search(pattern,plain)]}

def scan_site(name,url,previous=None):
    result={'name':name,'url':url,'checkedAt':stamp()}
    try:
        if not robots_allow(url):
            return {**result,'status':'blocked','error':'Skipped: robots policy does not allow this scan.'}
        details=page_details(fetch(url))
        digest=hashlib.sha256(json.dumps(details,sort_keys=True).encode()).hexdigest()
        return {**result,**details,'status':'ok','hash':digest,'changed':bool(previous and previous.get('hash') and previous['hash']!=digest)}
    except Exception as error:
        return {**result,'status':'unavailable','error':str(error)[:160]}

def scan_indicator(code,name,unit):
    url=f'https://api.worldbank.org/v2/country/BGD/indicator/{code}?format=json&per_page=70'
    result={'code':code,'name':name,'unit':unit,'url':f'https://data.worldbank.org/indicator/{code}?locations=BD','checkedAt':stamp()}
    try:
        payload=json.loads(fetch(url))
        rows=payload[1] if len(payload)>1 and isinstance(payload[1],list) else []
        latest=next((r for r in rows if r.get('value') is not None),None)
        if not latest:
            raise ValueError('No observation available')
        return {**result,'status':'ok','value':latest['value'],'year':latest['date']}
    except Exception as error:
        return {**result,'status':'unavailable','error':str(error)[:160]}

def topic_matches(title,topic):
    title=title.lower()
    if topic=='games': return bool(re.search(r'retro gam|physical gam|game discs|game dvds',title))
    if not re.search(r'bangladesh|dhaka',title): return False
    if topic=='creator': return bool(re.search(r'influencer|creator|digital marketing|ugc',title) and re.search(r'marketing|creator|social media|\bads\b|advertis|campaign',title))
    if topic=='clothing': return bool(re.search(r'fashion|retail|clothing|apparel|garment',title))
    if topic=='agriculture': return bool(re.search(r'agricultur|fisher|farm|aquaculture',title))
    return False

def parse_feed(text,topic,now=None):
    root=ET.fromstring(text)
    now=now or datetime.now(timezone.utc)
    rows=[]
    for item in root.findall('./channel/item'):
        link=item.findtext('link') or ''
        if urllib.parse.urlparse(link).scheme!='https':
            continue
        if not topic_matches(item.findtext('title') or '',topic): continue
        try:
            published=parsedate_to_datetime(item.findtext('pubDate') or '')
            if not published.tzinfo: published=published.replace(tzinfo=timezone.utc)
            if not 0 <= (now-published).total_seconds() <= 30*86400: continue
        except (ValueError,TypeError):
            continue
        rows.append({'topic':topic,'title':clean(item.findtext('title')),'url':link,'publishedAt':item.findtext('pubDate') or '', 'source':clean(item.findtext('source') or 'Google News',8)})
        if len(rows)==5: break
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='public/research-snapshot.json')
    args=parser.parse_args()
    path=Path(args.output)
    previous=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    old={row['url']:row for row in previous.get('competitors',[])}
    snapshot={'version':1,'checkedAt':stamp(),'competitors':[],'indicators':[],'headlines':[],'feedStatus':[]}
    for name,url in SITES:
        snapshot['competitors'].append(scan_site(name,url,old.get(url)))
        time.sleep(1)
    for code,name,unit in INDICATORS:
        snapshot['indicators'].append(scan_indicator(code,name,unit))
    for topic,query in TOPICS:
        url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query+' when:30d','hl':'en-US','gl':'BD','ceid':'BD:en'})
        status={'topic':topic,'checkedAt':stamp()}
        try:
            snapshot['headlines'].extend(parse_feed(fetch(url),topic))
            status['status']='ok'
        except Exception as error:
            status.update(status='unavailable',error=str(error)[:160])
        snapshot['feedStatus'].append(status)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(path),'competitors':{r['name']:r['status'] for r in snapshot['competitors']},'indicators':sum(r['status']=='ok' for r in snapshot['indicators']),'headlines':len(snapshot['headlines'])}))

if __name__=='__main__':
    main()
