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
