import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

import build_datasets as builder  # noqa: E402

DATA = ROOT / 'data'
DB = json.loads((DATA / 'NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026.json').read_text(encoding='utf-8'))


def read_csv(name):
    with open(DATA / name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def test_source_ids_unique_and_contiguous():
    ids = [s['source_id'] for s in DB['sources']]
    assert len(ids) == len(set(ids))
    assert ids == [f'S{i:04d}' for i in range(1, len(ids) + 1)]


def test_company_park_name_derived_from_id():
    by_id = {p['park_id']: p['park_name'] for p in DB['it_parks']}
    for company in DB['companies']:
        pid = company.get('it_park_id')
        assert company['it_park_name'] == (by_id.get(pid) if pid else None), company['company_id']


def test_company_names_have_no_newlines():
    assert all('\n' not in c['company_name'] and '\r' not in c['company_name']
               for c in DB['companies'])


def test_no_excluded_or_building_names_in_companies():
    bad_words = ('it park', 'cyber park', 'digital zone', 'business tower',
                 'world trade tower', 'signature tower')
    for company in DB['companies']:
        name = company['company_name'].lower()
        assert not any(word in name for word in bad_words), name
        if not company['company_id'].startswith('OSM'):
            continue
        for pattern, _reason in builder.EXCLUDE_RULES:
            if any(token in builder.norm_name(name) for token in builder.ALLOW_RAW):
                continue
            assert not __import__('re').search(pattern, name, __import__('re').I), (name, pattern)


def test_coordinate_quality_present_for_all_parks():
    assert len(DB['it_parks']) == 50
    assert all(p.get('coordinate_quality') for p in DB['it_parks'])


def test_unverified_records_have_no_last_verified():
    for company in DB['companies']:
        if company['verification_status'] in ('OSM_LISTED_UNVERIFIED', 'SEED_LEAD'):
            assert company['last_verified'] is None, company['company_id']
        assert company['last_checked'], company['company_id']
    assert all(loc['last_verified'] is None for loc in DB['company_locations'])
    assert all(park['last_verified'] is None for park in DB['it_parks'])


def test_seed_sources_are_not_labelled_osm():
    for source in DB['sources']:
        if source['supports'].startswith('SEED'):
            assert 'OSM' not in source['source_type']
            assert source['source_url'] is None


def test_scoring_has_no_substring_ai_signals():
    for name, domain, stack in [
        ('RateGain', 'Travel technology SaaS', []),
        ('Retail', 'Retail technology SaaS', []),
        ('Airflow Systems', None, ['Airflow']),
    ]:
        text = ' '.join([name, domain or '', ' '.join(stack)])
        assert not builder.has_ai_signal(text), name


def test_list_fields_match_between_csv_and_json():
    csv_rows = {r['company_id']: r for r in read_csv('NOIDA_GREATER_NOIDA_MASTER_COMPANIES_2026.csv')}
    json_rows = {c['company_id']: c for c in DB['companies']}
    assert set(csv_rows) == set(json_rows)
    for cid, row in csv_rows.items():
        for field in ('tech_stack', 'programming_languages', 'backend_technologies',
                      'frontend_technologies', 'databases', 'data_engineering_stack',
                      'ai_ml_stack', 'cloud_devops_stack', 'other_technologies'):
            csv_list = [v for v in row[field].split('; ') if v]
            assert csv_list == json_rows[cid][field], (cid, field)


def test_metadata_uses_v2_reference_date():
    assert DB['metadata']['research_date'] == builder.DEFAULT_AS_OF == '2026-11-20'
    assert DB['metadata']['total_parks'] == len(DB['it_parks']) == 50
    assert DB['metadata']['total_unique_companies'] == len(DB['companies'])


def test_student_fit_score_uses_all_five_v2_components():
    base = {'company_name': 'Example Systems', 'business_domain': None, 'tech_stack': []}
    assert builder.score(base) == 0
    assert builder.score({**base, 'business_domain': 'Data analytics'}) == 30
    assert builder.score({**base, 'company_name': 'Java Backend Solutions'}) == 20
    assert builder.score({**base, 'entry_level_roles': ['Backend Intern'],
                          'hiring_verified_date': '2026-11-20'}) == 25
    assert builder.score({**base, 'direct_application_url': 'https://example.com/apply'}) == 15
    assert builder.score({**base, 'tech_stack': ['Docker'],
                          'technology_evidence_source': 'https://example.com/stack'}) == 10
    assert builder.score({**base, 'business_domain': 'AI data',
                          'company_name': 'Python Backend',
                          'entry_level_roles': ['ML Intern'],
                          'hiring_verified_date': '2026-11-20',
                          'direct_application_url': 'https://example.com/apply',
                          'tech_stack': ['Python'],
                          'technology_evidence_source': 'https://example.com/stack'}) == 100
    for c in DB['companies']:
        assert 0 <= c['student_fit_score'] <= 100
        assert c['student_fit_score'] == builder.score(c)


def test_v2_required_columns_are_present():
    park_cols = set(read_csv('NOIDA_GREATER_NOIDA_TOP_50_IT_PARKS_2026.csv')[0])
    company_cols = set(read_csv('NOIDA_GREATER_NOIDA_MASTER_COMPANIES_2026.csv')[0])
    location_cols = set(read_csv('NOIDA_GREATER_NOIDA_COMPANY_LOCATIONS_2026.csv')[0])
    assert {'park_id', 'park_name', 'alternative_names', 'location_category', 'tier', 'city',
            'sector', 'full_address', 'latitude', 'longitude', 'nearest_metro',
            'operational_status', 'property_owner', 'property_manager', 'total_building_count',
            'verified_company_count', 'verified_mnc_count', 'verified_product_company_count',
            'verified_fintech_count', 'verified_it_service_count', 'gcc_presence',
            'major_tenants', 'technology_specializations', 'ranking_score',
            'ranking_explanation', 'official_website', 'contact_number', 'source_urls',
            'verification_status', 'last_verified'} <= park_cols
    assert {'company_id', 'company_name', 'brand_name', 'company_category',
            'secondary_categories', 'business_domain', 'headquarters', 'noida_office_status',
            'it_park_id', 'it_park_name', 'sector', 'building_name', 'tower',
            'full_office_address', 'office_phone', 'official_website', 'linkedin_url',
            'careers_url', 'internship_url', 'direct_application_url', 'programming_languages',
            'backend_technologies', 'frontend_technologies', 'databases',
            'data_engineering_stack', 'ai_ml_stack', 'cloud_devops_stack',
            'other_technologies', 'tech_stack_confidence', 'tenant_verification_source',
            'technology_evidence_source', 'contact_source', 'careers_source',
            'verification_status', 'last_verified', 'student_fit_score', 'entry_level_roles',
            'eligible_2028_batch', 'hiring_verified_date'} <= company_cols
    assert {'company_id', 'park_id', 'company_name', 'park_name', 'building_name', 'tower',
            'floor', 'office_address', 'tenant_status', 'occupancy_evidence', 'evidence_url',
            'evidence_date', 'verification_confidence', 'last_verified'} <= location_cols


def test_dashboard_excludes_data_only_fields_and_has_raw_fallback():
    sources = ''.join(p.read_text(encoding='utf-8') for p in
                      (ROOT / 'dashboard').rglob('*') if p.suffix in ('.js', '.html', '.css'))
    for field in ('full_address', 'full_office_address', 'office_phone', 'property_owner',
                  'property_manager', 'total_building_count', 'contact_number',
                  'building_name', 'office_address', 'lease', 'rent', 'floor', 'tower'):
        assert not __import__('re').search(r'\b' + field + r'\b', sources, __import__('re').I), field
    app = (ROOT / 'dashboard/js/app.js').read_text(encoding='utf-8')
    assert app.index('NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026.json') < app.index('noida_it_companies.json')


def test_reports_match_generated_counts():
    dq = (ROOT / 'reports' / 'DATA_QUALITY_REPORT_2026.md').read_text(encoding='utf-8')
    meta = DB['metadata']
    assert f"| Unique companies in master file | {meta['total_unique_companies']} |" in dq
    assert f"| Company-location relationships | {meta['total_company_locations']} |" in dq
    assert f"| Evidence sources in register | {meta['total_sources']} |" in dq
    ranking = (ROOT / 'reports' / 'TOP_50_IT_PARKS_RANKING_2026.md').read_text(encoding='utf-8')
    assert f"{len(builder.RANKING_CRITERIA)} criteria" in ranking
    assert 'eight criteria' not in ranking
    stack_report = (ROOT / 'reports' / 'TECHNOLOGY_STACK_REPORT_2026.md').read_text(encoding='utf-8')
    assert '| Go |' in stack_report
    assert '| verified_entry_level | 25 | 0 |' in stack_report
    assert '| offcampus_direct_apply | 15 | 0 |' in stack_report
