# Noida & Greater Noida IT Ecosystem 2026

Research snapshot for internship and job targeting (3rd-year B.Tech CSE AI & ML, ABES Engineering College).

## Important status

External web research was unavailable in the build environment (web-search rate limits / bot challenges).
The collector's Overpass query fails over across mirrors with retries; **no park, company, technology
stack, career link or location claim in this build has been independently verified**. Every record is a lead.

- 50 candidate park/hub locations
- 92 unique company leads (46 OSM listings, 46 from the supplied brief)
- 60 company-to-location relationships (51 unverified, 9 historical claims)
- 43 approximate map coordinates from OpenStreetMap Nominatim
- 13 stack chip sets, all `PUBLICLY_REPORTED` from careers-page text matching; none `VERIFIED`
- 15 careers links from collected pages
- 185 evidence-source rows with unique, contiguous IDs
- `student_fit_score` on every company: max 60/100 here because no live entry-level opening (25 pts)
  or off-campus direct application (15 pts) could be verified

See `reports/DATA_QUALITY_REPORT_2026.md` before using this data for applications.

## Run the collector

From the project root (no machine-specific paths are required):

```powershell
python scripts\noida_it_collector.py --enrich --limit 200 --out-dir data
```

Raw outputs are written to `data/noida_it_companies.csv` and `data/noida_it_companies.json`.
The builder uses the repo-local Nominatim cache at `data/cache/park_geocodes.json`. Rebuild all
final datasets **and all reports** with:

```powershell
python scripts\build_datasets.py --as-of 2026-11-20
```
`--as-of` defaults to `2026-11-20` (the v2 research reference date); reports are generated from the data, not hand-edited.

## Run the dashboard

Serve from the project root (fetch does not work on `file://`):

```powershell
cd NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026
python -m http.server 8000
```

Open `http://localhost:8000/dashboard/index.html`. The dashboard loads the final JSON first and falls
back to the raw collector JSON if it is missing. It includes park sector/ranking filters, stack quick
views (Java, Python, Spring Boot, React, data engineering, AI/ML, cloud/DevOps, fintech technology),
tier-coloured map markers, pagination, and `Unverified` badges for OSM discovery rows.

## Layout

- `scripts/` — collector and dataset builder/report generator
- `data/` — raw collector output, geocode cache, and the four final datasets
- `dashboard/` — dynamic HTML/CSS/JS dashboard
- `reports/` — ranking, classification, stack, fintech/product and data-quality reports
- `sources/` — source register

## Field policy

Property, tenancy-floor, street-address and phone/contact fields are retained in CSV files only and are
not rendered by the dashboard. The dashboard shows only parks, companies, stacks, opportunities,
evidence links and verification status.
