# Tarka Collective preview

Live preview: https://ahmedmasum2000000.github.io/tarka-collective-preview/

This repository contains the compiled static app. The source repository remains private at AhmedMasum2000000/Tarka-collective.

Built from source commit b97e302239a5aa7b2da89838845a294c4656b1e3. Type checking, 18 app tests, 8 scanner tests and the production build passed before publication. Calculator edits/saving, task reassignment, live market refresh, reference search, source saving and responsive layouts were checked in the browser.

## Current prototype

Manage ventures, ideas, plans, ROI scenarios, tasks, team assignments, finance records and approval gates in one dashboard. Data stays in each visitor's browser. Shared accounts and a shared database are not connected in this version.

All seeded ventures remain on execution hold. Planning scenarios are estimates, not recorded revenue or promised returns.

## Updating

Build the private source and publish its dist files here, retaining scripts/crawl-research.py and .github/workflows/research-pages.yml. GitHub Pages uses the workflow deployment. The public-source scanner runs hourly and deploys the latest snapshot alongside the app. Manual scans are available in Actions; schedules can be delayed. The Geist font license is included in geist-font-license.txt.

The app's Research refresh updates live World Bank observations and loads the latest scan. Wikipedia reference and GDELT news searches are on demand. Unavailable sources are shown as unavailable; saved sources remain for review. The scanner respects competitor robots policies, checks fixed public homepages and includes only headlines from the last 30 days.