# Data Quality Report 2026

Research reference date: 2026-11-20. All figures below are computed from the generated files.

## Executive summary

External verification was not possible in this build environment: web research was rate limited or
bot-challenged, and Nominatim geocoding produced only sector-level approximations. The collector
fails over across Overpass mirrors; no successful 504-retry event is claimed here. Consequently
**this dataset is a lead list, not a verified intelligence database**.

## Counts

| Metric | Value |
|---|---:|
| Total discovered / candidate locations | 50 |
| Total qualified locations (provisional) | 50 |
| Verified locations | 0 |
| Raw OSM company leads collected | 118 |
| Raw leads excluded as non-IT / non-company / duplicate | 72 |
| Unique companies in master file | 92 |
| Unique companies from OSM leads | 46 |
| Unique companies from research brief | 46 |
| Duplicate records removed (normalized) | 0 |
| Company-location relationships | 60 |
| Unverified tenant claims | 51 |
| Historical tenant claims | 9 |
| Verified current tenants | 0 |
| Parks with approximate coordinates | 43 of 50 |
| Evidence sources in register | 185 |

## Verification of stacks and opportunities

| Field | Count |
|---|---:|
| VERIFIED stack sets | 0 |
| PUBLICLY REPORTED stack sets | 13 |
| INFERRED stack sets | 0 |
| UNKNOWN stack sets | 79 |
| Careers links captured | 15 |
| Internship links captured | 0 |
| Direct application links captured | 0 |
| Verified entry-level openings | 0 |
| Verified 2028-batch flags | 0 |

## Missing data

| Field | Missing of 92 |
|---|---:|
| Office phone | 73 |
| Official website | 66 |
| Careers URL | 77 |
| LinkedIn URL | 75 |
| Stack evidence URL | 79 |

## Source register

| Source type | Rows |
|---|---:|
| OSM approximate geocode | 43 |
| OSM discovery lead | 46 |
| Research brief park lead | 50 |
| Seed lead (research brief) | 46 |

Source IDs are contiguous and unique (`S0001`–`S0185`). Research-brief seed leads
carry `source_type = "Seed lead (research brief)"` and a null `source_url`; the brief reference is
retained in the title and evidence statement. Prose references in park source rows are deliberately
not converted into URLs.

## Coordinate quality

| coordinate_quality | Parks |
|---|---:|
| APPROXIMATE_OSM_NOMINATIM_UNVERIFIED | 43 |
| NONE | 7 |

`coordinate_quality` is present on every park record in both CSV and JSON. Coordinates are
sector-level Nominatim approximations, not verified campus locations, and several parks share a
single centroid; the dashboard applies display-only jitter and labels them approximate.

## Exclusion log

Every raw lead omitted from the company master is listed with its reason. Park and building names
are represented on the parks side, not as companies.

| Raw ID | Name | Reason |
|---|---|---|
| C0007 | Honda Motorcycle & Scooter India Pvt. Ltd. Central Regional Office | automotive / vehicle services |
| C0008 | Sahahara News Network Office | media / news office |
| C0013 | KENT RO SYSTEMS LTD | construction / building systems / non-technology |
| C0019 | Design Parichay | no technology signal in name |
| C0020 | Centre for Studies of Plural Societies | association / foundation / non-technology body |
| C0024 | FastInfo Class | institution / education / hospitality |
| C0025 | Copper Tracks LLP | no technology signal in name |
| C0026 | R.S.ENTERPRISES UPVC DOOR AND WINDOW | non-technology manufacturing / retail |
| C0027 | New Era Dairy Engineers (I) Pvt Ltd. | non-technology manufacturing / retail |
| C0028 | Obeetee Pvt Ltd - Carpet & Rug Manufacturer India | non-technology manufacturing / retail |
| C0033 | Amigas Pharma | non-technology manufacturing / retail |
| C0035 | Agrawal Pankaj & Associates | CA Firm | association / foundation / non-technology body |
| C0036 | IndoSealer | no technology signal in name |
| C0040 | Mariinox | Vehicle Scrapper | Car Scrap Dealer | automotive / vehicle services |
| C0041 | Kachroo Design Consultants Pvt. Ltd. | no technology signal in name |
| C0044 | Globus IT Park | park / building name, not a company |
| C0046 | Smartwork Corporate Park | park / building name, not a company |
| C0049 | Emblogic | no technology signal in name |
| C0050 | Easy Street Consulting Private Limited | no technology signal in name |
| C0052 | Axis House | no technology signal in name |
| C0053 | Yamuna Expressway Industrial Development Authority | authority / government body |
| C0054 | Supertech Eco Mart | trading / advertising / facilities / non-technology lead |
| C0055 | Acropolis IT Park | park / building name, not a company |
| C0056 | Logix Cyber Park Blcok -A | park / building name, not a company |
| C0057 | Logix Cyber Park Blcok -B | park / building name, not a company |
| C0058 | Logix Cyber Park Blcok - C & D | park / building name, not a company |
| C0060 | Network 18 | known non-technology brand or duplicate brand listing |
| C0062 | Vodafone | known non-technology brand or duplicate brand listing |
| C0064 | Romsons International | no technology signal in name |
| C0065 | NSEZ Gate 2 | railway / government / labour office |
| C0066 | NSEZ Gate 1 | railway / government / labour office |
| C0067 | Muthoot finance | known non-technology brand or duplicate brand listing |
| C0068 | Supertone Cassette Industry | non-technology manufacturing / retail |
| C0071 | Waman Products Private Limited | no technology signal in name |
| C0072 | School Expert | institution / education / hospitality |
| C0074 | KGS Building Systems Pvt. Ltd. | construction / building systems / non-technology |
| C0075 | Pinakin Green Energy Pvt Ltd | trading / advertising / facilities / non-technology lead |
| C0078 | BSNL Office | railway / government / labour office |
| C0079 | Cars24 Financial Services | known non-technology brand or duplicate brand listing |
| C0080 | Avogardo | no technology signal in name |
| C0081 | Gulshan | no technology signal in name |
| C0082 | Uttariya Railway Mazdoor Union Office | railway / government / labour office |
| C0083 | S.S.E/WORKS/ANVT | railway / government / labour office |
| C0084 | Fino Payments Bank | known non-technology brand or duplicate brand listing |
| C0085 | Uttarakhand Handicrafts | non-technology manufacturing / retail |
| C0086 | ASP Enterprises | trading / advertising / facilities / non-technology lead |
| C0087 | Global Advertising | trading / advertising / facilities / non-technology lead |
| C0088 | S.R.S. Enterprises | trading / advertising / facilities / non-technology lead |
| C0089 | R.B. Traders | trading / advertising / facilities / non-technology lead |
| C0090 | HCL | duplicate of a separately seeded brand |
| C0091 | Paras Enterprises | trading / advertising / facilities / non-technology lead |
| C0093 | T.D. & Sons Printing Solution | trading / advertising / facilities / non-technology lead |
| C0094 | Masha Telecom Solutions | trading / advertising / facilities / non-technology lead |
| C0095 | Bajaj Finserv | known non-technology brand or duplicate brand listing |
| C0097 | National Labour Cooperative Federation of India Limited | association / foundation / non-technology body |
| C0098 | Planetcast Media Services Limited | media / news office |
| C0100 | Uppal Group | trading / advertising / facilities / non-technology lead |
| C0101 | EssilorLuxottica | no technology signal in name |
| C0103 | Simon India Ltd. | known non-technology brand or duplicate brand listing |
| C0105 | ION Digital Zone IDZ 1 | park / building name, not a company |
| C0106 | Barco Electronic Systems Pvt. Ltd. | known non-technology brand or duplicate brand listing |
| C0107 | Seltech Metal Building & Roofing Solution | construction / building systems / non-technology |
| C0108 | Sensorise Digital Services Pvt Ltd | trading / advertising / facilities / non-technology lead |
| C0109 | Pinnacle Business Tower | park / building name, not a company |
| C0110 | World Trade Tower | park / building name, not a company |
| C0111 | Adobe Systems India Pvt Ltd | duplicate of a separately seeded brand |
| C0112 | ION Digital Zone IDZ 2 | park / building name, not a company |
| C0113 | Paharpur Cooling Towers ltd | construction / building systems / non-technology |
| C0115 | Beta AV Systems Pvt. Ltd. | trading / advertising / facilities / non-technology lead |
| C0116 | India Trading - Interactive Flat panel display, Video Conferencing equipments | trading / advertising / facilities / non-technology lead |
| C0117 | Utility Powertech Limited | trading / advertising / facilities / non-technology lead |
| C0118 | Vardhman Signature Tower | park / building name, not a company |

## Link checks

No automated HTTP validation of external links was performed. URL-valued evidence comes from the
collector output; research-brief leads are labelled as such and have no URL. All links must be
checked manually before use.

## QA checklist results

- Duplicate park names: none (50 unique IDs/names).
- Duplicate company records: none after normalized deduplication.
- Company-to-park links: 60, all retained with explicit tenant status.
- All companies joined to parks by `it_park_id`; `it_park_name` is derived from the park record.
- JSON syntax and CSV column consistency validated by `tests/test_data.py`.
- Historical tenants: 9 links marked Historical, never Current.
- Unverified OSM, seed and park records have a null `last_verified`; `last_checked` is the build date.
- Excluded UI fields: no lease, floor, tower, street-address, property-owner or phone fields are rendered.

## Research limitations

1. No access to Level 1 corporate real-estate disclosures (REIT investor material, SEZ records).
2. No access to official careers or engineering pages beyond those the collector happened to fetch.
3. No live job-posting verification, so internship/hiring fields are null.
4. Nominatim resolved several named parks to sector centroids; all coordinates carry an explicit
   `coordinate_quality` value or are null.
5. Sector-level "hubs" may not qualify as single office campuses under a stricter reading of the brief.
6. Only 92 of the requested 150-250 companies could be assembled as leads; none are verified.
