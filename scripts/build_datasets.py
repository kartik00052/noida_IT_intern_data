#!/usr/bin/env python3
"""Builds the final Noida/Greater Noida datasets and reports from repo-local inputs only.

Inputs (no fabricated records):
  data/noida_it_companies.json       - raw collector output (OSM discovery leads)
  data/cache/park_geocodes.json      - Nominatim coordinate lookups, approximate
  Section 3.1 of the user brief      - seed park/company names (candidate leads only)

Every output record is marked unverified unless evidence exists in the inputs.
All report figures are computed from the generated data.
"""
import argparse
import ast
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
CACHE = DATA / 'cache' / 'park_geocodes.json'
REPORTS = ROOT / 'reports'
SOURCES = ROOT / 'sources'
DEFAULT_AS_OF = '2026-11-20'

PARK_TIER = {
    'P01': 'A', 'P07': 'A', 'P08': 'A', 'P11': 'C', 'P12': 'C',
    'P13': 'A', 'P14': 'A', 'P15': 'A', 'P17': 'A', 'P18': 'B',
    'P21': 'A', 'P22': 'A', 'P23': 'A', 'P24': 'A', 'P25': 'A',
    'P26': 'B', 'P28': 'B', 'P29': 'B', 'P30': 'B', 'P35': 'B',
    'P41': 'D', 'P42': 'D', 'P43': 'D', 'P44': 'D', 'P45': 'D', 'P46': 'D',
}

PARK_CATEGORY = {
    'P01': 'IT Park', 'P02': 'IT Park', 'P03': 'IT Park', 'P04': 'Business Park',
    'P05': 'Business Park', 'P06': 'Business Park', 'P07': 'IT Hub / Sector Cluster',
    'P08': 'IT Hub / Sector Cluster', 'P09': 'Technology Cluster',
    'P10': 'IT Hub / Sector Cluster', 'P11': 'IT/ITES SEZ', 'P12': 'IT/ITES SEZ',
    'P13': 'IT Hub / Sector Cluster', 'P14': 'Technology Campus',
    'P15': 'IT Park', 'P16': 'Business Park', 'P17': 'IT Hub / Sector Cluster',
    'P18': 'Business Park', 'P19': 'Business Park', 'P20': 'Business Park',
    'P21': 'IT Park', 'P22': 'IT Hub / Sector Cluster',
    'P23': 'Technology Cluster', 'P24': 'Corporate Campus',
    'P25': 'Corporate Campus', 'P26': 'Business Park', 'P27': 'IT Park',
    'P28': 'IT Hub / Sector Cluster', 'P29': 'Technology Campus',
    'P30': 'R&D Cluster', 'P31': 'Corporate Cluster',
    'P32': 'IT Hub / Sector Cluster', 'P33': 'Corporate Corridor',
    'P34': 'Emerging Technology Cluster', 'P35': 'Corporate Corridor',
    'P36': 'Commercial Office Cluster', 'P37': 'Emerging Technology Cluster',
    'P38': 'Emerging Technology Cluster', 'P39': 'Emerging Technology Cluster',
    'P40': 'Corporate Office Cluster', 'P41': 'Knowledge Park / Emerging IT',
    'P42': 'Knowledge Park / Emerging IT', 'P43': 'Knowledge Park / Emerging IT',
    'P44': 'Knowledge Park / Emerging IT', 'P45': 'Knowledge Park / Emerging IT',
    'P46': 'Technology Zone', 'P47': 'Commercial Office Cluster',
    'P48': 'Industrial Technology Area', 'P49': 'Industrial Technology Area',
    'P50': 'Emerging Technology Corridor',
}

SEED_PRIORITY = {
    'P01': 1, 'P07': 2, 'P08': 2, 'P21': 3, 'P23': 4, 'P14': 5,
    'P26': 6, 'P15': 7, 'P29': 8, 'P12': 9, 'P41': 10, 'P42': 10,
    'P43': 10, 'P44': 10, 'P45': 10, 'P46': 10,
}

SEED_COMPANIES = [
    ('Adobe', 'Product-Based', ['P24'], 'Creative software'),
    ('Microsoft', 'Product-Based', [], 'Cloud and productivity software'),
    ('Samsung R&D', 'Product-Based', [], 'Consumer electronics and semiconductor R&D'),
    ('Oracle', 'Product-Based', [], 'Enterprise software and databases'),
    ('Synopsys', 'Semiconductor', ['P29'], 'Electronic design automation'),
    ('Nokia', 'Product-Based', [], 'Telecommunications and networking'),
    ('IndiaMART', 'Product-Based', ['P18'], 'B2B marketplace'),
    ('Info Edge', 'Product-Based', ['P23'], 'Online classifieds and recruitment'),
    ('Innovaccer', 'AI/ML', ['P01'], 'Healthcare AI and data platform'),
    ('RateGain', 'Product-Based', [], 'Travel technology SaaS'),
    ('Barclays', 'Banking Technology', ['P01'], 'Banking and financial technology'),
    ('Pine Labs', 'Fintech', ['P01'], 'Payment infrastructure'),
    ('Paytm', 'Fintech', [], 'Payments and financial services'),
    ('ION Trading', 'Fintech', ['P01'], 'Financial trading software'),
    ('Xceedance', 'Fintech', [], 'Insurance technology services'),
    ('Acidaes Solutions', 'Fintech', [], 'Insurance technology'),
    ('Landis+Gyr', 'Industrial Technology', ['P01'], 'Smart metering and grid technology'),
    ('HCLTech', 'IT Services', ['P14'], 'IT services and engineering'),
    ('TCS', 'IT Services', [], 'IT services and consulting'),
    ('Wipro', 'IT Services', ['P15', 'P44'], 'IT services and consulting'),
    ('Tech Mahindra', 'IT Services', ['P02', 'P12', 'P15'], 'IT services and consulting'),
    ('Cognizant', 'IT Services', ['P20', 'P21'], 'IT services and consulting'),
    ('Accenture', 'IT Services', ['P04', 'P21', 'P23'], 'IT services and consulting'),
    ('Capgemini', 'IT Services', ['P12'], 'IT services and consulting'),
    ('Infosys', 'IT Services', ['P23', 'P25'], 'IT services and consulting'),
    ('IBM', 'IT Services', ['P04', 'P20'], 'Enterprise technology and consulting'),
    ('Nagarro', 'Digital Engineering', [], 'Digital engineering'),
    ('GlobalLogic', 'Digital Engineering', ['P26'], 'Digital engineering'),
    ('UST', 'IT Services', ['P03'], 'Digital technology services'),
    ('Sopra Steria', 'IT Services', [], 'IT services and consulting'),
    ('Genpact', 'BPO/ITES', ['P21', 'P23', 'P46'], 'Business process and technology services'),
    ('TO THE NEW', 'Digital Engineering', ['P27'], 'Digital engineering and cloud'),
    ('Appinventiv', 'Software Development', [], 'Mobile and product engineering'),
    ('Attentive AI', 'AI/ML', [], 'Artificial intelligence software'),
    ('Publicis Sapient', 'Digital Engineering', ['P26'], 'Digital transformation consulting'),
    ('Axtria', 'Data Analytics', [], 'Life sciences data analytics'),
    ('Birlasoft', 'IT Services', ['P46'], 'Enterprise IT services'),
    ('Vinculum', 'Product-Based', [], 'Retail technology SaaS'),
    ('Amazon', 'Product-Based', ['P01'], 'Cloud and e-commerce technology'),
    ('Mindtree', 'IT Services', ['P01'], 'IT services and engineering'),
    ('Black Box', 'IT Services', ['P18'], 'IT infrastructure services'),
    ('Xavient', 'IT Services', ['P21'], 'IT services and testing'),
    ('MetLife', 'Banking Technology', ['P26'], 'Insurance technology operations'),
    ('EXL', 'Data Analytics', ['P26'], 'Analytics and business process services'),
    ('NTT DATA', 'IT Services', ['P26', 'P46'], 'IT services and consulting'),
    ('Coforge', 'IT Services', ['P46'], 'IT services and engineering'),
]

EXCLUDE_RULES = [
    (r'\bnewspaper\b|\bnews\b|\bmedia services\b', 'media / news office'),
    (r'\bhospital\b|\bhotels?\b|\bschools?\b|\bcolleges?\b|\binstitutes?\b|\buniversit(?:y|ies)\b|\bfastinfo\b', 'institution / education / hospitality'),
    (r'\bfoundation\b|\bassociation\b|\bassociates\b|\bcentre for studies\b|\bcooperative federation\b', 'association / foundation / non-technology body'),
    (r'\breal estate\b|\bconstruction\b|\bro systems?\b|\bbuilding systems\b|\bmetal building\b|\broofing\b|\bcooling towers?\b', 'construction / building systems / non-technology'),
    (r'\bhonda\b|\bmotorcycle\b|\bscooter\b|\bvehicle scrapper\b|\bcar scrap\b', 'automotive / vehicle services'),
    (r'\brestaurant\b|\btravel agent\b|\bdairy\b|\bcarpet\b|\brug\b|\bpharma\b|\bupvc\b|\bdoor and window\b|\bcassette\b|\bhandicrafts?\b', 'non-technology manufacturing / retail'),
    (r'\blabour\b|\brailway mazdoor\b|\bgate [12]\b|\brailway\b|\bs\.s\.e\b|\bbsnl\b|\bpostal\b', 'railway / government / labour office'),
    (r'\bit park\b|\bcyber park\b|\bbusiness park\b|\bcorporate park\b|\bdigital zone\b|\bbusiness tower\b|\bworld trade tower\b|\bsignature tower\b|\btech park\b', 'park / building name, not a company'),
    (r'\beco mart\b|\bpowertech\b|\bcabinet\b|\bprinting solution\b|\badvertising\b|\btraders?\b|\benterprises\b|\bgroup\b|\bsolar\b|\bgreen energy\b|\bav systems\b|\binteractive flat panel\b|\btelecom solutions\b|\bsensorise\b', 'trading / advertising / facilities / non-technology lead'),
    (r'\bsimon india\b|\bessilor\b|\bbajaj finserv\b|\bmuthoot\b|\bfino payments\b|\bcars24\b|\bvodafone\b|\bnetwork 18\b|\bplanetcast\b|\bbarco\b|\bahuja\b|\bpure software\b|\bthird eye\b|\bsignatures\b|\bsupertech\b|\bdisplays?\b', 'known non-technology brand or duplicate brand listing'),
    (r'\badobe systems\b|\bhcl\b|\bniit technologies\b|\bhcltech\b', 'duplicate of a separately seeded brand'),
    (r'\byamuna expressway industrial\b|\bs.S\.E\b|\beducational\b', 'authority / government body'),
]

INCLUDE_RE = re.compile(
    r'tech|soft|info|digital|data|cloud|cyber|analytic|systems?|web|\bapp\b|dev|lab|solution|'
    r'network|seo|uav|\bit\b|\bai\b|\bml\b|fin|semi|electronic|robot', re.I)

ALLOW_RAW = {
    'stannik', 'railyatri', 'teamvariance', 'lambdatest', 'esrirdcentre',
    'vidooly', 'interrainformation', 'niit', 'arohaninfocare', 'kyisolutions',
    'credentsolutions', 'wae', 'geosys', 'trackobit', 'uthoplatforms', 'rohdeschwarz',
    'refabelectrochip',
}

AI_PATTERNS = [r'\bai\b', r'\bml\b', r'\bllm\b', r'\bmachine learning\b', r'\bdata\b',
               r'\banalytics?\b', r'\bpython\b', r'\bpytorch\b', r'\btensorflow\b',
               r'\bnlp\b', r'\brag\b', r'\blangchain\b', r'\bvision\b']
BACKEND_PATTERNS = [r'\bjava\b', r'\bpython\b', r'\bspring\b', r'\bfastapi\b',
                    r'\bdjango\b', r'\bflask\b', r'\bbackend\b', r'\bmicroservices?\b']

LIST_FIELDS = ['programming_languages', 'backend_technologies', 'frontend_technologies',
               'databases', 'data_engineering_stack', 'ai_ml_stack', 'cloud_devops_stack',
               'other_technologies', 'tech_stack', 'entry_level_roles', 'alternative_names']

PARK_FIELDS = ['park_id', 'park_name', 'alternative_names', 'location_category', 'tier',
    'city', 'sector', 'full_address', 'latitude', 'longitude', 'nearest_metro',
    'operational_status', 'property_owner', 'property_manager', 'total_building_count',
    'verified_company_count', 'verified_mnc_count', 'verified_product_company_count',
    'verified_fintech_count', 'verified_it_service_count', 'gcc_presence', 'major_tenants',
    'technology_specializations', 'ranking_score', 'ranking_explanation', 'official_website',
    'contact_number', 'source_urls', 'verification_status', 'last_verified', 'last_checked',
    'coordinate_quality']

COMPANY_FIELDS = ['company_id', 'company_name', 'alt_names', 'brand_name', 'company_category',
    'secondary_categories', 'business_domain', 'headquarters', 'noida_office_status',
    'it_park_id', 'it_park_name', 'sector', 'building_name', 'tower', 'full_office_address',
    'office_phone', 'official_website', 'linkedin_url', 'careers_url', 'internship_url',
    'direct_application_url', 'programming_languages', 'backend_technologies',
    'frontend_technologies', 'databases', 'data_engineering_stack', 'ai_ml_stack',
    'cloud_devops_stack', 'other_technologies', 'tech_stack', 'tech_stack_confidence',
    'tenant_verification_source', 'technology_evidence_source', 'contact_source',
    'careers_source', 'verification_status', 'last_verified', 'last_checked',
    'student_fit_score', 'entry_level_roles', 'eligible_2028_batch', 'hiring_verified_date']

LOC_FIELDS = ['company_id', 'park_id', 'company_name', 'park_name', 'building_name', 'tower',
    'floor', 'office_address', 'tenant_status', 'occupancy_evidence', 'evidence_url',
    'evidence_date', 'verification_confidence', 'last_verified', 'last_checked']

SOURCE_FIELDS = ['source_id', 'source_url', 'source_title', 'source_type', 'evidence_statement',
    'access_date', 'publication_date', 'confidence_level', 'supports']

RANKING_CRITERIA = [
    ('Verified technology companies', 25),
    ('MNCs and GCCs', 15),
    ('Product companies and fintech', 15),
    ('Software engineering / R&D relevance', 15),
    ('Diversity of technology companies', 10),
    ('Operational infrastructure and office scale', 10),
    ('Internship and employment relevance', 10),
]


def norm_name(name):
    return re.sub(r'\b(pvt|private|ltd|limited|india|llp|inc|technologies|technology)\b|[^a-z0-9]',
                  '', str(name).lower())


def clean_name(value):
    raw = str(value or '')
    lines = [re.sub(r'\s+', ' ', line).strip() for line in raw.splitlines()]
    latin = ''.join(ch for ch in (lines[0] if lines else '') if ord(ch) < 128)
    latin = re.sub(r'\s+', ' ', latin).strip()
    alt = ' | '.join(line for line in lines[1:] if line) or None
    return latin, alt


def has_ai_signal(text):
    return any(re.search(pattern, text, re.I) for pattern in AI_PATTERNS)


SCORE_WEIGHTS = {
    'ai_data_python': 30,
    'java_python_backend': 20,
    'verified_entry_level': 25,
    'offcampus_direct_apply': 15,
    'stack_evidence': 10,
}


def score_flags(company):
    text = ' '.join(str(v) for v in [company.get('company_name') or '',
            company.get('business_domain') or '', ' '.join(company.get('tech_stack') or [])]).lower()
    roles = company.get('entry_level_roles') or []
    return {
        'ai_data_python': has_ai_signal(text),
        'java_python_backend': any(re.search(p, text, re.I) for p in BACKEND_PATTERNS),
        'verified_entry_level': bool(company.get('hiring_verified_date') and
                                     (roles or company.get('internship_url'))),
        'offcampus_direct_apply': bool(company.get('direct_application_url')),
        'stack_evidence': bool(company.get('tech_stack') and company.get('technology_evidence_source')),
    }


def score(company):
    flags = score_flags(company)
    return min(sum(SCORE_WEIGHTS[k] for k, v in flags.items() if v), 100)


def write_csv(path, fields, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for row in rows:
            out = {}
            for key in fields:
                value = row.get(key)
                if isinstance(value, list):
                    value = '; '.join(str(v) for v in value)
                out[key] = '' if value is None else value
            w.writerow(out)


def write_report(name, text):
    (REPORTS / name).write_text(text.rstrip() + '\n', encoding='utf-8')


def collector_tech_keywords():
    tree = ast.parse((ROOT / 'scripts' / 'noida_it_collector.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'TECH' for t in node.targets):
            return list(ast.literal_eval(node.value).keys())
    return []


def build_seed_associations():
    assoc = defaultdict(list)
    historical_at_p21 = {'Cognizant', 'Genpact', 'Accenture', 'Samsung', 'Xavient'}
    for name, _cat, park_ids, _domain in SEED_COMPANIES:
        for pid in park_ids:
            historical = (pid == 'P21' and name in historical_at_p21) or pid == 'P26'
            status = 'Historical' if historical else 'Unverified'
            note = 'Section 3.1: reported/historical' if historical else 'Section 3.1 seed lead'
            assoc[pid].append((name, status, note))
    return assoc


def generate_reports(stats, parks, companies, locations, sources, raw, exclusions, tech_keywords):
    counts = Counter(c['company_category'] for c in companies)
    conf = Counter(c['tech_stack_confidence'] for c in companies)
    tenants = Counter(l['tenant_status'] for l in locations)
    src_types = Counter(s['source_type'] for s in sources)
    coord = Counter(p['coordinate_quality'] for p in parks)
    missing = {
        'Office phone': sum(1 for c in companies if not c['office_phone']),
        'Official website': sum(1 for c in companies if not c['official_website']),
        'Careers URL': sum(1 for c in companies if not c['careers_url']),
        'LinkedIn URL': sum(1 for c in companies if not c['linkedin_url']),
        'Stack evidence URL': sum(1 for c in companies if not c['technology_evidence_source']),
    }
    careers = sum(1 for c in companies if c['careers_url'])
    intern = sum(1 for c in companies if c['internship_url'])
    direct = sum(1 for c in companies if c['direct_application_url'])
    score_hits = Counter()
    for c in companies:
        for key, hit in score_flags(c).items():
            if hit:
                score_hits[key] += 1
    with_coords = sum(1 for p in parks if p['latitude'] is not None)
    excluded_rows = '\n'.join(
        f'| {cid} | {name} | {reason} |' for cid, name, reason in exclusions) or '| — | — | none |'
    coord_rows = '\n'.join(f'| {k} | {v} |' for k, v in sorted(coord.items()))
    cat_rows = '\n'.join(f'| {k} | {v} |' for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    src_rows = '\n'.join(f'| {k} | {v} |' for k, v in sorted(src_types.items()))

    write_report('DATA_QUALITY_REPORT_2026.md', f"""# Data Quality Report 2026

Research reference date: {stats['as_of']}. All figures below are computed from the generated files.

## Executive summary

External verification was not possible in this build environment: web research was rate limited or
bot-challenged, and Nominatim geocoding produced only sector-level approximations. The collector
fails over across Overpass mirrors; no successful 504-retry event is claimed here. Consequently
**this dataset is a lead list, not a verified intelligence database**.

## Counts

| Metric | Value |
|---|---:|
| Total discovered / candidate locations | {stats['parks']} |
| Total qualified locations (provisional) | {stats['parks']} |
| Verified locations | {stats['verified_parks']} |
| Raw OSM company leads collected | {stats['raw']} |
| Raw leads excluded as non-IT / non-company / duplicate | {stats['excluded']} |
| Unique companies in master file | {stats['companies']} |
| Unique companies from OSM leads | {stats['osm_companies']} |
| Unique companies from research brief | {stats['seed_companies']} |
| Duplicate records removed (normalized) | {stats['duplicates']} |
| Company-location relationships | {stats['locations']} |
| Unverified tenant claims | {tenants.get('Unverified', 0)} |
| Historical tenant claims | {tenants.get('Historical', 0)} |
| Verified current tenants | {tenants.get('Current', 0)} |
| Parks with approximate coordinates | {with_coords} of {stats['parks']} |
| Evidence sources in register | {stats['sources']} |

## Verification of stacks and opportunities

| Field | Count |
|---|---:|
| VERIFIED stack sets | {conf.get('VERIFIED', 0)} |
| PUBLICLY REPORTED stack sets | {conf.get('PUBLICLY_REPORTED', 0)} |
| INFERRED stack sets | {conf.get('INFERRED', 0)} |
| UNKNOWN stack sets | {conf.get('UNKNOWN', 0)} |
| Careers links captured | {careers} |
| Internship links captured | {intern} |
| Direct application links captured | {direct} |
| Verified entry-level openings | {sum(1 for c in companies if c['entry_level_roles'])} |
| Verified 2028-batch flags | {sum(1 for c in companies if c['eligible_2028_batch'])} |

## Missing data

| Field | Missing of {stats['companies']} |
|---|---:|
{chr(10).join(f'| {k} | {v} |' for k, v in missing.items())}

## Source register

| Source type | Rows |
|---|---:|
{src_rows}

Source IDs are contiguous and unique (`S0001`–`S{stats['sources']:04d}`). Research-brief seed leads
carry `source_type = "Seed lead (research brief)"` and a null `source_url`; the brief reference is
retained in the title and evidence statement. Prose references in park source rows are deliberately
not converted into URLs.

## Coordinate quality

| coordinate_quality | Parks |
|---|---:|
{coord_rows}

`coordinate_quality` is present on every park record in both CSV and JSON. Coordinates are
sector-level Nominatim approximations, not verified campus locations, and several parks share a
single centroid; the dashboard applies display-only jitter and labels them approximate.

## Exclusion log

Every raw lead omitted from the company master is listed with its reason. Park and building names
are represented on the parks side, not as companies.

| Raw ID | Name | Reason |
|---|---|---|
{excluded_rows}

## Link checks

No automated HTTP validation of external links was performed. URL-valued evidence comes from the
collector output; research-brief leads are labelled as such and have no URL. All links must be
checked manually before use.

## QA checklist results

- Duplicate park names: none ({stats['parks']} unique IDs/names).
- Duplicate company records: none after normalized deduplication.
- Company-to-park links: {stats['locations']}, all retained with explicit tenant status.
- All companies joined to parks by `it_park_id`; `it_park_name` is derived from the park record.
- JSON syntax and CSV column consistency validated by `tests/test_data.py`.
- Historical tenants: {tenants.get('Historical', 0)} links marked Historical, never Current.
- Unverified OSM, seed and park records have a null `last_verified`; `last_checked` is the build date.
- Excluded UI fields: no lease, floor, tower, street-address, property-owner or phone fields are rendered.

## Research limitations

1. No access to Level 1 corporate real-estate disclosures (REIT investor material, SEZ records).
2. No access to official careers or engineering pages beyond those the collector happened to fetch.
3. No live job-posting verification, so internship/hiring fields are null.
4. Nominatim resolved several named parks to sector centroids; all coordinates carry an explicit
   `coordinate_quality` value or are null.
5. Sector-level "hubs" may not qualify as single office campuses under a stricter reading of the brief.
6. Only {stats['companies']} of the requested 150-250 companies could be assembled as leads; none are verified.
""")

    priority = sorted(SEED_PRIORITY.items(), key=lambda kv: (kv[1], kv[0]))
    priority_text = ' · '.join(
        f'{rank} {next(p["park_name"] for p in parks if p["park_id"] == pid)}' for pid, rank in priority)
    named = [p for p in parks if p['city'] == 'Noida']
    greater = [p for p in parks if p['city'] != 'Noida']
    write_report('TOP_50_IT_PARKS_RANKING_2026.md', f"""# Top {stats['parks']} IT Parks / Hubs — Provisional Ranking ({stats['as_of'][:4]})

**Status: unscored candidate list.** The brief's ranking methodology (100 points across
{len(RANKING_CRITERIA)} criteria) cannot be applied without verified tenant counts, MNC/GCC counts,
product/fintech counts, infrastructure evidence and hiring data. In this environment none of those
were available, so `ranking_score` is null for all {stats['parks']} rows. The order below is the order
of discovery from the brief and the OSM collector, not a quality ranking.

## Methodology that should be applied after verification

| Criterion | Weight |
|---|---:|
{chr(10).join(f'| {name} | {weight} |' for name, weight in RANKING_CRITERIA)}
| **Total** | **{sum(w for _, w in RANKING_CRITERIA)}** |

Provisional tiers in the dataset are based only on how the brief describes each location:
Tier A = established IT/technology park or hub, Tier B = business park with expected IT tenants,
Tier C = SEZ/technology campus, Tier D = emerging knowledge/tech zone, Tier E = single building or
small office cluster. These are labelled provisional and must be re-checked.

## Candidate locations

### Noida — named parks, campuses and hubs
{', '.join(p['park_name'] for p in named)}.

### Greater Noida
{', '.join(p['park_name'] for p in greater)}.

### Priority order from the brief (not an evidence-based score)
{priority_text}.

## Exclusions / uncertainty

Several entries are sector-level hubs rather than single campuses (as permitted by the brief). A number of
emerging-sector entries were included only because the brief names the sector range; they have no verified
technology tenancy in this build and should be the first candidates to drop if fewer than {stats['parks']}
qualify.
""")

    status_rows = '\n'.join(
        f'| {k} | {v} |' for k, v in sorted(Counter(c['verification_status'] for c in companies).items()))
    write_report('COMPANY_CLASSIFICATION_REPORT_2026.md', f"""# Company Classification Report {stats['as_of'][:4]}

Generated from `data/NOIDA_GREATER_NOIDA_MASTER_COMPANIES_2026.csv` on {stats['as_of']}.
All {stats['companies']} records are leads; none are independently verified.

## Category distribution

| Category | Companies |
|---|---:|
{cat_rows}

## Verification status

| Status | Companies |
|---|---:|
{status_rows}

## Notes

- {stats['osm_companies']} records come from OSM discovery leads and {stats['seed_companies']} from
  the supplied research brief; research-brief records use `source_type = "Seed lead (research brief)"`.
- Park and building names are not classified as companies; they are represented in the parks dataset.
- All company-to-park associations use `it_park_id`; `it_park_name` is derived from the park record.
- Non-Latin source names are retained in `alt_names`; `company_name` is the clean Latin form.
""")

    product = [c for c in companies if c['company_category'] == 'Product-Based']
    seed_semiconductor = [c for c in companies if c['company_category'] == 'Semiconductor'
                          and c['company_id'].startswith('SEED')]
    product_rd = product + seed_semiconductor
    fin = [c for c in companies if c['company_category'] in ('Fintech', 'Banking Technology')]
    product_lines = '\n'.join(f'- {c["company_name"]} ({c["company_category"]})' for c in product_rd)
    fin_lines = '\n'.join(f'- {c["company_name"]} ({c["company_category"]})' for c in fin)
    write_report('FINTECH_AND_PRODUCT_COMPANIES_2026.md', f"""# Fintech and Product Companies {stats['as_of'][:4]}

Generated from the master company file on {stats['as_of']}. Counts below are derived from
`company_category`; no record was reclassified for this report.

## Fintech and banking technology ({len(fin)} leads)

{fin_lines}

## Product / R&D ({len(product_rd)} leads)

This group is the {len(product)} `Product-Based` records plus the
{len(seed_semiconductor)} research-brief `Semiconductor` product/R&D record(s). OSM semiconductor
component leads are listed separately in `COMPANY_CLASSIFICATION_REPORT_2026.md`, so the grouping is
explicit and every listed category can be checked against the master file.

{product_lines}

Adjacent but not counted here: `AI/ML`, `SaaS`, `Data Analytics` and OSM `Semiconductor` records are
reported in `COMPANY_CLASSIFICATION_REPORT_2026.md`.
""")

    tech_counts = Counter(t for c in companies for t in c['tech_stack'])
    tech_rows = '\n'.join(f'| {t} | {tech_counts.get(t, 0)} |' for t in tech_keywords)
    write_report('TECHNOLOGY_STACK_REPORT_2026.md', f"""# Technology Stack Report {stats['as_of'][:4]}

Generated from the master company file on {stats['as_of']}. A stack is listed only when the source
record carries public evidence; `UNKNOWN` means no reliable evidence was captured.

## Search vocabulary

The collector searches {len(tech_keywords)} technologies (the `TECH` map in
`scripts/noida_it_collector.py`, including Go). Counts of companies whose captured stack contains
each term:

| Technology | Companies |
|---|---:|
{tech_rows}

## Confidence distribution

| Confidence | Companies |
|---|---:|
{chr(10).join(f'| {k} | {v} |' for k, v in sorted(conf.items()))}

## Scoring note

`student_fit_score` is the sum of five v2 components: AI/ML/Data/Python relevance 30,
Java/Python backend relevance 20, verified entry-level or internship opening 25, off-campus direct
application 15, and presence of stack evidence 10. Component hits in this build:

| Component | Weight | Companies matching |
|---|---:|---:|
{chr(10).join(f'| {k} | {SCORE_WEIGHTS[k]} | {score_hits[k]} |' for k in SCORE_WEIGHTS)}

No live job posting was verifiable, so the 25-point opening component is 0 for every row; no direct
application URL was available, so the 15-point component is also 0. Word-boundary matching prevents
"RateGain", "Retail" and "Airflow" from producing an AI signal. Tests live in `tests/test_data.py`.
""")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', default=DEFAULT_AS_OF,
                        help=f'build/reference date (default: {DEFAULT_AS_OF})')
    args = parser.parse_args()
    as_of = args.as_of

    with open(DATA / 'noida_it_companies.json', encoding='utf-8') as f:
        raw = json.load(f)['companies']
    with open(CACHE, encoding='utf-8') as f:
        geos = {g['park_id']: g for g in json.load(f)}

    parks = []
    for pid, g in geos.items():
        src = []
        if g['geocode_source']:
            src.append(f"OSM Nominatim approximate geocode: {g['geocode_source']}")
        src.append('User brief Section 3.1 (candidate lead)')
        priority = SEED_PRIORITY.get(pid)
        explanation = (
            f'Provisional only: seed priority {priority} from user brief Section 3.1. '
            'No verified tenant counts, MNC counts or operational evidence available; '
            'ranking_score intentionally null.'
        ) if priority else (
            'Provisional only: candidate location from user brief. No verified tenant, '
            'operational or scale evidence available in this environment; '
            'ranking_score intentionally null.'
        )
        parks.append({
            'park_id': pid, 'park_name': g['park_name'], 'alternative_names': None,
            'location_category': PARK_CATEGORY[pid], 'tier': PARK_TIER.get(pid, 'E'),
            'city': g['city'], 'sector': g['sector'], 'full_address': None,
            'latitude': g['latitude'], 'longitude': g['longitude'], 'nearest_metro': None,
            'operational_status': None, 'property_owner': None, 'property_manager': None,
            'total_building_count': None, 'verified_company_count': 0,
            'verified_mnc_count': 0, 'verified_product_company_count': 0,
            'verified_fintech_count': 0, 'verified_it_service_count': 0,
            'gcc_presence': None, 'major_tenants': None, 'technology_specializations': None,
            'ranking_score': None, 'ranking_explanation': explanation,
            'official_website': None, 'contact_number': None,
            'source_urls': ' | '.join(src), 'verification_status': 'UNVERIFIED_CANDIDATE',
            'last_verified': None, 'last_checked': as_of,
            'coordinate_quality': 'APPROXIMATE_OSM_NOMINATIM_UNVERIFIED' if g['latitude'] else 'NONE',
        })
    assert all(p['coordinate_quality'] for p in parks), 'coordinate_quality missing on a park'
    park_name_by_id = {p['park_id']: p['park_name'] for p in parks}
    assert len(park_name_by_id) == len(parks)

    park_by_raw = {
        'Sector 62 IT Hub': 'P07', 'Sector 63 / 64 Hub': 'P08', 'Noida SEZ (NSEZ)': 'P11',
        'Sector 125 Hub': 'P13', 'Sector 126-132 Corridor': 'P14',
        'Knowledge Park Greater Noida': 'P41', 'Greater Noida West': 'P47',
        'Logix': 'P03', 'Stellar': 'P02', 'Assotech': 'P19',
        'Galaxy Business': 'P05', 'It Park': None,
    }

    seed_assoc = build_seed_associations()
    companies = []
    locations = []
    exclusions = []
    dedupe = {}
    duplicates = 0

    for raw_row in raw:
        name, alt = clean_name(raw_row['company_name'])
        key = norm_name(name)
        low = name.lower()
        allow = any(token in key for token in ALLOW_RAW)
        reason = None
        if not allow:
            for pattern, why in EXCLUDE_RULES:
                if re.search(pattern, low, re.I):
                    reason = why
                    break
            if reason is None and not INCLUDE_RE.search(low):
                reason = 'no technology signal in name'
        if reason:
            exclusions.append((raw_row['company_id'], name, reason))
            continue
        if key in dedupe:
            duplicates += 1
            exclusions.append((raw_row['company_id'], name, 'duplicate of ' + dedupe[key]))
            continue
        dedupe[key] = f"OSM{raw_row['company_id'][1:]}"
        cid = f"OSM{raw_row['company_id'][1:]}"
        stack = raw_row.get('tech_stack') or []
        confidence = raw_row.get('tech_confidence') or 'UNKNOWN'
        if not stack:
            confidence = 'UNKNOWN'
        pid = park_by_raw.get(raw_row.get('park_name'))
        comp = {
            'company_id': cid, 'company_name': name, 'alt_names': alt, 'brand_name': None,
            'company_category': raw_row['company_category'] or 'IT Services',
            'secondary_categories': None, 'business_domain': None,
            'headquarters': None, 'noida_office_status': 'Unverified OSM listing',
            'it_park_id': pid, 'it_park_name': park_name_by_id.get(pid),
            'sector': None, 'building_name': None, 'tower': None,
            'full_office_address': raw_row.get('address'), 'office_phone': raw_row.get('phone'),
            'official_website': raw_row.get('website'), 'linkedin_url': raw_row.get('linkedin_url'),
            'careers_url': raw_row.get('careers_url'), 'internship_url': None,
            'direct_application_url': None, 'programming_languages': stack,
            'backend_technologies': [], 'frontend_technologies': [], 'databases': [],
            'data_engineering_stack': [], 'ai_ml_stack': [], 'cloud_devops_stack': [],
            'other_technologies': [], 'tech_stack_confidence': confidence,
            'tenant_verification_source': raw_row.get('source'),
            'technology_evidence_source': raw_row.get('tech_evidence_url'),
            'contact_source': raw_row.get('source') if raw_row.get('phone') else None,
            'careers_source': raw_row.get('careers_url'),
            'verification_status': 'OSM_LISTED_UNVERIFIED', 'last_verified': None,
            'last_checked': as_of, 'tech_stack': stack, 'student_fit_score': 0,
            'entry_level_roles': None, 'eligible_2028_batch': None, 'hiring_verified_date': None,
        }
        comp['student_fit_score'] = score(comp)
        companies.append(comp)
        if pid:
            locations.append({
                'company_id': cid, 'park_id': pid, 'company_name': name,
                'park_name': park_name_by_id[pid], 'building_name': None, 'tower': None,
                'floor': None, 'office_address': None, 'tenant_status': 'Unverified',
                'occupancy_evidence': 'OSM listing only; not independently verified',
                'evidence_url': raw_row.get('source'), 'evidence_date': None,
                'verification_confidence': 'UNVERIFIED', 'last_verified': None,
                'last_checked': as_of,
            })

    for idx, (name, cat, park_ids, domain) in enumerate(SEED_COMPANIES, 1):
        key = norm_name(name)
        if key in dedupe:
            duplicates += 1
            exclusions.append((f'SEED{idx:03d}', name, 'duplicate of ' + dedupe[key]))
            continue
        dedupe[key] = f'SEED{idx:03d}'
        cid = f'SEED{idx:03d}'
        pid = park_ids[0] if park_ids else None
        comp = {
            'company_id': cid, 'company_name': name, 'alt_names': None, 'brand_name': None,
            'company_category': cat, 'secondary_categories': None, 'business_domain': domain,
            'headquarters': None, 'noida_office_status': 'Unverified seed lead',
            'it_park_id': pid, 'it_park_name': park_name_by_id.get(pid),
            'sector': None, 'building_name': None, 'tower': None, 'full_office_address': None,
            'office_phone': None, 'official_website': None, 'linkedin_url': None,
            'careers_url': None, 'internship_url': None, 'direct_application_url': None,
            'programming_languages': [], 'backend_technologies': [], 'frontend_technologies': [],
            'databases': [], 'data_engineering_stack': [], 'ai_ml_stack': [],
            'cloud_devops_stack': [], 'other_technologies': [], 'tech_stack_confidence': 'UNKNOWN',
            'tenant_verification_source': 'User brief Section 3.1',
            'technology_evidence_source': None, 'contact_source': None, 'careers_source': None,
            'verification_status': 'SEED_LEAD', 'last_verified': None, 'last_checked': as_of,
            'tech_stack': [], 'student_fit_score': 0, 'entry_level_roles': None,
            'eligible_2028_batch': None, 'hiring_verified_date': None,
        }
        comp['student_fit_score'] = score(comp)
        companies.append(comp)
        for link_pid in park_ids:
            for assoc_name, status, note in seed_assoc.get(link_pid, []):
                if assoc_name == name:
                    locations.append({
                        'company_id': cid, 'park_id': link_pid, 'company_name': name,
                        'park_name': park_name_by_id[link_pid], 'building_name': None,
                        'tower': None, 'floor': None, 'office_address': None,
                        'tenant_status': status, 'occupancy_evidence': note,
                        'evidence_url': None, 'evidence_date': None,
                        'verification_confidence': 'UNVERIFIED' if status != 'Historical' else 'HISTORICAL_CLAIM',
                        'last_verified': None, 'last_checked': as_of,
                    })

    for comp in companies:
        pid = comp.get('it_park_id')
        expected = park_name_by_id.get(pid) if pid else None
        if pid is not None:
            assert expected is not None, f'unknown park id {pid} on {comp["company_id"]}'
        assert comp['it_park_name'] == expected, f'stale park name on {comp["company_id"]}'
    assert all('\n' not in c['company_name'] for c in companies)

    sources = []
    def add_source(source_url, title, source_type, statement, supports):
        sources.append({
            'source_id': f'S{len(sources) + 1:04d}', 'source_url': source_url,
            'source_title': title, 'source_type': source_type,
            'evidence_statement': statement, 'access_date': as_of, 'publication_date': None,
            'confidence_level': 'UNVERIFIED', 'supports': supports,
        })

    for p in parks:
        for url in p['source_urls'].split(' | '):
            if not url:
                continue
            add_source(
                url, f"Location evidence for {p['park_name']}",
                'OSM approximate geocode' if 'Nominatim' in url else 'Research brief park lead',
                'Candidate location only; no verified technology tenancy or operational status.',
                p['park_id'])
    for comp in companies:
        if not comp['tenant_verification_source']:
            continue
        is_seed = comp['verification_status'] == 'SEED_LEAD'
        add_source(
            None if is_seed else comp['tenant_verification_source'],
            (f"Research brief Section 3.1 lead for {comp['company_name']}" if is_seed
             else f"OSM listing for {comp['company_name']}"),
            'Seed lead (research brief)' if is_seed else 'OSM discovery lead',
            ('Section 3.1 candidate lead; physical tenancy and technology stack not independently verified.'
             if is_seed else
             'Discovery lead only; physical tenancy and current operation not independently verified.'),
            comp['company_id'])
    expected_ids = [f'S{i:04d}' for i in range(1, len(sources) + 1)]
    assert [s['source_id'] for s in sources] == expected_ids, 'source ids are not unique and contiguous'
    assert len({s['source_id'] for s in sources}) == len(sources)

    write_csv(DATA / 'NOIDA_GREATER_NOIDA_TOP_50_IT_PARKS_2026.csv', PARK_FIELDS, parks)
    write_csv(DATA / 'NOIDA_GREATER_NOIDA_MASTER_COMPANIES_2026.csv', COMPANY_FIELDS, companies)
    write_csv(DATA / 'NOIDA_GREATER_NOIDA_COMPANY_LOCATIONS_2026.csv', LOC_FIELDS, locations)
    write_csv(SOURCES / 'SOURCE_REGISTER_2026.csv', SOURCE_FIELDS, sources)

    json_parks = []
    for p in parks:
        q = {k: p[k] for k in PARK_FIELDS if k not in ['full_address', 'property_owner',
             'property_manager', 'total_building_count', 'contact_number']}
        q['source_urls'] = [u for u in p['source_urls'].split(' | ') if u]
        q['data_only_note'] = ('Property/address/contact fields exist in CSV only and are omitted '
                               'from the dashboard per Section 0.1.')
        json_parks.append(q)

    json_companies = []
    for c in companies:
        q = {k: c[k] for k in COMPANY_FIELDS if k not in ['building_name', 'tower',
             'full_office_address', 'office_phone', 'contact_source']}
        for k in LIST_FIELDS:
            if k in q and not isinstance(q[k], list):
                q[k] = []
        q['tech_stack'] = list(c['tech_stack'])
        json_companies.append(q)

    json_locs = [{k: l[k] for k in LOC_FIELDS if k not in ['building_name', 'tower',
                 'floor', 'office_address']} for l in locations]

    db = {
        'metadata': {
            'research_date': as_of, 'build_date': as_of,
            'region': 'Noida and Greater Noida, Uttar Pradesh, India',
            'total_parks': len(parks), 'total_unique_companies': len(companies),
            'total_company_locations': len(locations), 'total_sources': len(sources),
            'verification_policy': 'Evidence-based; no unverified lead is presented as verified.',
            'data_warning': ('External web research was unavailable in this environment. '
                'All park/company records are candidates/unverified. Coordinates are approximate '
                'OSM geocodes. No ranking scores, career openings, tech stacks or evidence links '
                'were invented. See reports/DATA_QUALITY_REPORT_2026.md.'),
            'dashboard_fields_excluded': ['full_address', 'property_owner', 'property_manager',
                'total_building_count', 'contact_number', 'building_name', 'tower', 'floor',
                'office_address', 'office_phone', 'contact_source'],
        },
        'it_parks': json_parks, 'companies': json_companies,
        'company_locations': json_locs, 'sources': sources,
    }
    with open(DATA / 'NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    stats = {
        'as_of': as_of, 'parks': len(parks), 'companies': len(companies),
        'locations': len(locations), 'sources': len(sources), 'raw': len(raw),
        'excluded': len(exclusions), 'duplicates': duplicates,
        'osm_companies': sum(1 for c in companies if c['verification_status'] == 'OSM_LISTED_UNVERIFIED'),
        'seed_companies': sum(1 for c in companies if c['verification_status'] == 'SEED_LEAD'),
        'verified_parks': sum(1 for p in parks if p['verification_status'] == 'VERIFIED'),
    }
    generate_reports(stats, parks, companies, locations, sources, raw, exclusions,
                     collector_tech_keywords())

    print(f"parks={len(parks)} companies={len(companies)} locations={len(locations)} "
          f"sources={len(sources)} exclusions={len(exclusions)} as_of={as_of}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
