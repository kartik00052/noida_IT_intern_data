const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.resolve(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');
const css = read('dashboard/css/styles.css');
const data = JSON.parse(read('data/NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026.json'));

const dom = new JSDOM(read('dashboard/index.html'), {
  runScripts: 'outside-only',
  url: 'http://localhost:8000/dashboard/index.html',
  pretendToBeVisual: true,
});
const { window } = dom;
const doc = window.document;
window.fetch = () => new Promise(() => {});
const style = doc.createElement('style');
style.textContent = css;
doc.head.appendChild(style);
for (const file of ['app.js', 'filters.js', 'parks.js', 'companies.js', 'map.js']) {
  window.eval(read('dashboard/js/' + file));
}
doc.dispatchEvent(new window.Event('DOMContentLoaded'));
window.NG.state.data = data;
window.NG.renderAll();

const checks = [];
const check = (name, fn) => {
  try {
    fn();
    checks.push([name, 'PASS']);
  } catch (e) {
    checks.push([name, 'FAIL: ' + e.message]);
    process.exitCode = 1;
  }
};

check('modal is not visible on load', () => {
  const backdrop = doc.getElementById('modalBackdrop');
  assert.strictEqual(backdrop.hidden, true);
  assert.match(css, /\[hidden\]\s*\{[^}]*display:\s*none\s*!important/i);
  assert.doesNotMatch(css, /\.modal-backdrop\s*\{[^}]*display:\s*grid\s*!important/i);
});

check('tabs expose ARIA tablist/tab state and table headers have scope', () => {
  assert.ok(doc.querySelector('.tabs[role="tablist"]'));
  assert.strictEqual(doc.querySelectorAll('.tab[role="tab"]').length, 7);
  assert.ok(doc.querySelector('.tab[aria-selected="true"]'));
  assert.ok([...doc.querySelectorAll('th')].every((th) => th.getAttribute('scope') === 'col'));
});

check('career search filters the careers table', () => {
  const input = doc.getElementById('careerSearch');
  input.value = 'Adobe';
  input.dispatchEvent(new window.Event('input', { bubbles: true }));
  const rows = [...doc.querySelectorAll('#careerTable tbody tr')];
  assert.ok(rows.some((r) => r.textContent.includes('Adobe')), 'Adobe missing');
  assert.ok(!rows.some((r) => r.textContent.includes('Microsoft')), 'unfiltered row present');
  input.value = '';
  input.dispatchEvent(new window.Event('input', { bubbles: true }));
});

check('park profile shows joined technologies and opportunity count', () => {
  const byId = Object.fromEntries(data.companies.map((c) => [c.company_id, c]));
  const hit = data.company_locations
    .map((l) => ({ pid: l.park_id, company: byId[l.company_id] }))
    .find((x) => x.company && x.company.tech_stack.length && x.company.careers_url);
  assert.ok(hit, 'no park with a technology + careers link in the data');
  window.NGParks.profile(hit.pid);
  const body = doc.getElementById('modalBody').textContent;
  assert.ok(body.includes(hit.company.tech_stack[0]), 'technology missing from profile');
  assert.match(body, /[1-9]\d* linked company record\(s\)/, 'opportunity count is zero');
  window.NG.closeModal();
});

check('evidence column renders prose references instead of a bare dash', () => {
  const input = doc.getElementById('sourceSearch');
  input.value = 'User brief Section 3.1 (candidate lead)';
  input.dispatchEvent(new window.Event('input', { bubbles: true }));
  const rows = [...doc.querySelectorAll('#sourceTable tbody tr')];
  assert.ok(rows.length > 0, 'no prose-reference sources rendered');
  assert.ok(rows.every((r) => r.textContent.includes('Reference (no URL):')));
  input.value = '';
  input.dispatchEvent(new window.Event('input', { bubbles: true }));
});

check('all four confidence labels render distinct chips', () => {
  const labels = ['VERIFIED', 'PUBLICLY_REPORTED', 'INFERRED', 'UNKNOWN'];
  const classes = labels.map((l) => window.NG.stackChips(['X'], l).match(/chip-[a-z]+/)[0]);
  assert.strictEqual(new Set(classes).size, 4, classes.join(','));
  assert.strictEqual(classes[1], 'chip-reported');
});

check('filters reset pagination to page 1', () => {
  window.NG.state.page.parks = 3;
  const select = doc.getElementById('parkCity');
  select.value = 'Noida';
  select.dispatchEvent(new window.Event('change', { bubbles: true }));
  assert.strictEqual(window.NG.state.page.parks, 1);
  select.value = '';
  select.dispatchEvent(new window.Event('change', { bubbles: true }));
});

check('company park filter joins by it_park_id, not park name', () => {
  const select = doc.getElementById('companyPark');
  const option = [...select.options].find((o) => o.value);
  assert.ok(option, 'no park options');
  select.value = option.value;
  select.dispatchEvent(new window.Event('change', { bubbles: true }));
  const expected = data.companies.filter((c) => c.it_park_id === option.value).length;
  assert.ok(expected > 0, 'selected park has no companies');
  assert.strictEqual(doc.querySelectorAll('#companyTable tbody tr').length, Math.min(expected, 15));
  select.value = '';
  select.dispatchEvent(new window.Event('change', { bubbles: true }));
});

check('OSM discovery rows display an Unverified badge', () => {
  const badge = window.NG.statusBadge('OSM_LISTED_UNVERIFIED');
  assert.match(badge, /pill-warn/);
  assert.match(badge, />Unverified</);
});

check('default company sort is student_fit_score descending', () => {
  const sort = doc.getElementById('companySort');
  assert.strictEqual(sort.options[1].value, 'Student fit score');
  const rows = [...doc.querySelectorAll('#companyTable tbody tr')];
  const firstFit = Number(rows[0].children[5].textContent.trim());
  const best = Math.max(...data.companies.map((c) => c.student_fit_score || 0));
  assert.strictEqual(firstFit, best);
});

check('park sector and ranking filters work', () => {
  const sector = doc.getElementById('parkSector');
  const option = [...sector.options].find((o) => o.value);
  sector.value = option.value;
  sector.dispatchEvent(new window.Event('change', { bubbles: true }));
  const rows = [...doc.querySelectorAll('#parkTable tbody tr')];
  assert.ok(rows.length > 0);
  assert.ok(rows.every((r) => r.children[2].textContent.trim() === option.value));
  sector.value = '';
  sector.dispatchEvent(new window.Event('change', { bubbles: true }));
  const rank = doc.getElementById('parkRank');
  rank.value = 'Not scored';
  rank.dispatchEvent(new window.Event('change', { bubbles: true }));
  assert.ok(doc.querySelectorAll('#parkTable tbody tr').length > 0);
  rank.value = '';
  rank.dispatchEvent(new window.Event('change', { bubbles: true }));
});

check('tech stack quick views filter by preset', () => {
  const preset = doc.getElementById('stackPreset');
  preset.value = 'Java companies';
  preset.dispatchEvent(new window.Event('change', { bubbles: true }));
  assert.match(doc.getElementById('stackResults').innerHTML, /Java/);
  preset.value = 'Fintech technology companies';
  preset.dispatchEvent(new window.Event('change', { bubbles: true }));
  assert.match(doc.getElementById('stackResults').textContent, /Fintech|Banking Technology/);
  preset.value = '';
  preset.dispatchEvent(new window.Event('change', { bubbles: true }));
});

check('empty-state colspan matches each table column count', () => {
  for (const [inputId, tableId, key] of [
    ['companySearch', 'companyTable', 'companies'],
    ['careerSearch', 'careerTable', 'careers'],
  ]) {
    const input = doc.getElementById(inputId);
    input.value = 'zzzz-no-match';
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
    const table = doc.getElementById(tableId);
    const colspan = Number(table.querySelector('tbody td').getAttribute('colspan'));
    assert.strictEqual(colspan, table.querySelectorAll('thead th').length, tableId);
    assert.strictEqual(window.NG.state.page[key], 1);
    input.value = '';
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  }
  const search = doc.getElementById('sourceSearch');
  search.value = 'zzzz-no-match';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
  const sourceTable = doc.getElementById('sourceTable');
  assert.strictEqual(Number(sourceTable.querySelector('tbody td').getAttribute('colspan')),
    sourceTable.querySelectorAll('thead th').length);
  search.value = '';
  search.dispatchEvent(new window.Event('input', { bubbles: true }));
});

check('app keeps working when Leaflet is undefined', () => {
  assert.match(doc.getElementById('map').textContent, /Map unavailable/);
  assert.ok(doc.getElementById('statGrid').children.length > 0);
  assert.ok(doc.getElementById('noCoordsPanel').hidden === false);
  assert.match(doc.getElementById('noCoordsPanel').textContent, /Parks without coordinates/);
});

check('theme toggle exposes aria-pressed', () => {
  const toggle = doc.getElementById('themeToggle');
  assert.ok(['true', 'false'].includes(toggle.getAttribute('aria-pressed')));
});

async function checkRawFallback() {
  const raw = JSON.parse(read('data/noida_it_companies.json'));
  const dom2 = new JSDOM(read('dashboard/index.html'), {
    runScripts: 'outside-only',
    url: 'http://localhost:8000/dashboard/index.html',
    pretendToBeVisual: true,
  });
  const w = dom2.window;
  w.fetch = async (url) => url.includes('NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026.json')
    ? { ok: false }
    : { ok: true, json: async () => raw };
  for (const file of ['app.js', 'filters.js', 'parks.js', 'companies.js', 'map.js']) {
    w.eval(read('dashboard/js/' + file));
  }
  w.document.dispatchEvent(new w.Event('DOMContentLoaded'));
  await new Promise((r) => setTimeout(r, 50));
  assert.strictEqual(w.document.getElementById('dataStatus').textContent, 'Raw fallback data');
  assert.strictEqual(w.NG.state.rawFallback, true);
  assert.strictEqual(w.NG.state.data.companies.length, raw.companies.length);
  checks.push(['raw collector fallback loads when final JSON is missing', 'PASS']);
}

checkRawFallback().catch((e) => {
  checks.push(['raw collector fallback loads when final JSON is missing', 'FAIL: ' + e.message]);
  process.exitCode = 1;
}).then(() => {
  for (const [name, result] of checks) console.log(`${result === 'PASS' ? 'ok  ' : 'FAIL'} ${name}`);
  console.log(`${checks.filter((c) => c[1] === 'PASS').length}/${checks.length} dashboard checks passed`);
});
