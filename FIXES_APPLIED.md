# Fixes Applied — NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026

Build reference date: `2026-11-21`. All figures below were regenerated from repo-local inputs.
No data was invented; unverified records remain `UNKNOWN`, `OSM_LISTED_UNVERIFIED` or `SEED_LEAD`.

## Phase A — Dashboard breakages

| # | File(s) changed | Fix | Verification (command → result) |
|---|---|---|---|
| 1 | `dashboard/css/styles.css` | Added `[hidden]{display:none !important;}` so `.modal-backdrop{display:grid}` cannot override the `hidden` attribute. | `node tests/check_dashboard.js` → `ok modal is not visible on load` (hidden attr + CSS rule asserted). |
| 2 | `dashboard/js/filters.js` | `careerSearch` input now calls `NGCompanies.renderCareers()`. | `node tests/check_dashboard.js` → `ok career search filters the careers table`. |
| 3 | `dashboard/js/parks.js`, `dashboard/js/filters.js`, `dashboard/js/companies.js` | Location rows are joined to companies by `company_id`; fallback joins companies by `it_park_id`. The company park filter also selects by `it_park_id` (dropdown shows `park_name` only as a label). Technologies and opportunity count come from joined company records. | `node tests/check_dashboard.js` → `ok park profile shows joined technologies and opportunity count` and `ok company park filter joins by it_park_id, not park name`. |
| 4 | `dashboard/js/app.js` | `NG.link()` renders full URLs as anchors, prose references as `Reference (no URL): …` text, and only null/empty as a dash. | `node tests/check_dashboard.js` → `ok evidence column renders prose references instead of a bare dash`. |
| 5 | `dashboard/js/app.js` | Confidence labels normalized with `.replace(/_/g,' ')`; all four labels map to distinct chips. | `node tests/check_dashboard.js` → `ok all four confidence labels render distinct chips`. |

## Phase B — Data pipeline

| # | File(s) changed | Fix | Verification (command → result) |
|---|---|---|---|
| 6 | `scripts/build_datasets.py` | Single monotonic source counter; asserts IDs equal `S0001…Sxxxx` and are unique. | `python -m pytest tests/test_data.py -q` → `test_source_ids_unique_and_contiguous PASSED`; 185 rows, 185 unique IDs. |
| 7 | `scripts/build_datasets.py`, both company reports | Seed sources now `source_type="Seed lead (research brief)"`, brief-specific title, `source_url=null`. | `test_seed_sources_are_not_labelled_osm PASSED`; 46 seed sources, 0 with OSM type, 0 with a URL. |
| 8 | `scripts/build_datasets.py`, `reports/DATA_QUALITY_REPORT_2026.md` | `coordinate_quality` added to `PARK_FIELDS`, CSV and JSON; asserted non-empty on all 50 parks; report now prints the real distribution (43 approximate / 7 none). | `test_coordinate_quality_present_for_all_parks PASSED`; report contains `coordinate_quality` table. |
| 9 | `scripts/build_datasets.py` | `it_park_name` derived from `parks[it_park_id].park_name`; dangling `It Park` names removed; wrong `Sector 126-132 Corridor → P06` mapping corrected to `P14`. | `test_company_park_name_derived_from_id PASSED` → 0 mismatches. |
| 10 | `scripts/build_datasets.py`, `reports/DATA_QUALITY_REPORT_2026.md` | `EXCLUDE_NAME` replaced with word-boundary `EXCLUDE_RULES` + reasons, `\bit\b` include rule, explicit allow-list for genuine IT leads, park/building names removed from companies. Every excluded row is logged with a reason in the data-quality report. | `test_no_excluded_or_building_names_in_companies PASSED`; report Exclusion log has 72 rows; 0 FastInfo/Globus/Acropolis/Logix-block/ION-building records in company master. |
| 11 | `scripts/build_datasets.py` | AI scoring now uses `\bai\b`, `\bml\b`, `\bllm\b` and phrase boundaries. | `test_scoring_has_no_substring_ai_signals PASSED` for RateGain, Retail and Airflow. |
| 16 | `scripts/build_datasets.py`, `data/cache/park_geocodes.json`, `requirements.txt` | Geocode cache moved into repo; `--as-of` defaults to `2026-11-21`; pinned Python dependencies added. | `python scripts/build_datasets.py --help` shows `--as-of`; `python scripts/build_datasets.py` works with no machine-specific paths. |
| 17 | `scripts/build_datasets.py` | All list fields serialized with `; ` consistently; `tech_stack` added to master CSV; `clean_name()` strips newlines and keeps the original non-Latin text in `alt_names`. | `test_list_fields_match_between_csv_and_json PASSED`; `test_company_names_have_no_newlines PASSED`; 3 `alt_names` rows present. |
| 18 | `scripts/build_datasets.py` | `last_verified=null` for OSM, seed and park/location records; new `last_checked` holds the build date. | `test_unverified_records_have_no_last_verified PASSED`. |

## Phase C — Collector

| Change | File | Verification |
|---|---|---|
| `--out-dir` (default repo `data/`), written via `Path` | `scripts/noida_it_collector.py` | `python scripts/noida_it_collector.py --help` → `--out-dir OUT_DIR` listed. |
| Empty-result guard before `rows[0]` is used | `scripts/noida_it_collector.py` | Code inspection; `sys.exit(1)` with message before seed/save paths. |
| Overpass retry: 3 attempts per mirror with exponential backoff | `scripts/noida_it_collector.py` | Code inspection; warning text includes `attempt n/3`. |
| Go included in technology report | `scripts/build_datasets.py`, report | `test_reports_match_generated_counts PASSED` → `| Go |` present (count 0, from data). |

## Phase D — Map and UX

| Problem | File(s) | Fix / verification |
|---|---|---|
| CDN failure | `dashboard/js/map.js`, `dashboard/js/app.js` | `typeof L` guard + try/catch; fallback message `Map unavailable (CDN blocked)`; `renderAll()` wraps `NGMap.init()`. Verified by `node tests/check_dashboard.js` → `ok app keeps working when Leaflet is undefined`. |
| Legend collisions / dark mode | `dashboard/js/map.js`, `dashboard/css/styles.css` | Dedicated `.map-legend` with theme CSS variables. |
| Stacked markers / null coordinates | `dashboard/js/map.js`, `dashboard/index.html` | Deterministic display-only jitter for shared centroids; `#noCoordsPanel` lists the 7 parks with null coordinates. Dashboard check asserts panel populated. |
| Hardcoded colspan / no page reset | `dashboard/js/app.js`, `dashboard/js/filters.js` | Colspan computed from `thead th`; `NG.resetPage(key)` called on every filter/sort/search change. Dashboard checks pass for colspan and page reset. |
| Accessibility | `dashboard/index.html`, `dashboard/js/app.js`, `dashboard/css/styles.css` | Tablist/tab/tabpanel ARIA + arrow keys, `th scope="col"`, dialog focus save/trap/restore, theme `aria-pressed` + persisted `localStorage`, `:focus-visible`, `.btn-ghost`, `<noscript>`. Dashboard checks pass for ARIA and theme state. |

## Phase E/F — Reports, docs and cleanup

| Item | Fix / verification |
|---|---|
| All five reports regenerated by `generate_reports()` from the loaded data; no hand-typed counts. | `python scripts/build_datasets.py` → reports rewritten; `test_reports_match_generated_counts PASSED`. |
| Ranking report says **7** criteria, table totals 100. | Report inspection; test asserts `7 criteria` and no `eight criteria`. |
| Fintech/product report: product/R&D heading is **11** (10 `Product-Based` + 1 research-brief `Semiconductor` product/R&D record) and includes Vinculum. OSM semiconductor component leads are listed in the classification report. | Report inspection: `## Product / R&D (11 leads)`. |
| Technology report includes Go. | Report inspection: `| Go | 0 |`. |
| Overpass "504 then retry" narrative removed from README and data-quality report; retry is now actually implemented. | README/report inspection. |
| Low cleanup: dead `modalTitle` no-op removed, unused `.badge` CSS removed, tech options computed once, per-render listeners replaced with delegation, `file://` notice, persisted theme, `<noscript>`, `last_checked` shown in modals. | `node --check` on all dashboard JS; dashboard checks pass. |

## Baseline and full verification

```
python scripts\build_datasets.py
  → parks=50 companies=92 locations=60 sources=185 exclusions=72 as_of=2026-11-21

python -m pytest tests\test_data.py -q
  → 10 passed

node tests\check_dashboard.js
  → 11/11 dashboard checks passed

node --check dashboard\js\app.js (and companies/filters/map/parks.js)
  → all exit 0

python -c "json.load(...) for both JSONs; csv.reader(...) for all 5 CSVs"
  → both JSONs parse; all CSVs have uniform column counts
```

`run_all.ps1` runs collector → builder → data tests → dashboard checks → HTTP server;
use `.\run_all.ps1 -SkipCollector` to reuse the repo-local raw leads offline.

## Remaining known limitations

- The workspace is **not a git repository**, so `git diff --stat` cannot be produced. Changed files are
  limited to: `README.md`, `requirements.txt`, `run_all.ps1`, `FIXES_APPLIED.md`, all files under
  `dashboard/`, `scripts/`, `data/`, `reports/`, `sources/`, `tests/`, plus the new
  `data/cache/park_geocodes.json`.
- The collector still requires network access to Overpass and to company websites for `--enrich`;
  the checked-in raw leads and geocode cache make the builder and all tests fully offline/reproducible.
- `jsdom` is installed under `tests/node_modules` and is required only for the dashboard checks.
- The "11 product/R&D" grouping intentionally combines 10 `Product-Based` records with 1 research-brief
  `Semiconductor` product/R&D record; this is stated explicitly in the report so it can be checked
  against `company_category`. It does not reclassify any record.
- All records remain unverified leads; no external HTTP link validation or live careers verification was
  possible in this environment.
