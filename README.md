# Tarka Collective preview

Live preview: https://ahmedmasum2000000.github.io/tarka-collective-preview/

This repository contains only the compiled static preview. The source repository remains private at AhmedMasum2000000/Tarka-collective.

Built from source commit f8a5808e1d83d21c5407fdefccf8912d0bd85914. The production build and all 11 existing tests passed before publication.

## Current prototype

Manage ventures, ideas, plans, ROI scenarios, tasks, team assignments, finance records and approval gates in one dashboard. Data is saved in each visitor's browser. Shared accounts and a shared database are not connected in this version.

All seeded ventures remain on execution hold. Planning scenarios are estimates, not recorded revenue or promised returns.

## Updating the preview

Build the source with `npm ci`, `npm test`, and `npm run build`. Publish the contents of `dist/` here alongside `.nojekyll`. GitHub Pages serves the `main` branch from the repository root.