window.NGFilters = (function () {
  const sel = (id, label, options, anyLabel) => `
    <select id="${id}" aria-label="${label}">
      <option value="">${anyLabel}</option>
      ${options.map(o => `<option value="${NG.esc(o)}">${NG.esc(o)}</option>`).join('')}
    </select>`;

  const selPairs = (id, label, pairs, anyLabel) => `
    <select id="${id}" aria-label="${label}">
      <option value="">${anyLabel}</option>
      ${pairs.map(([v, l]) => `<option value="${NG.esc(v)}">${NG.esc(l)}</option>`).join('')}
    </select>`;

  function unique(field, list) {
    return [...new Set(list.map(x => x[field]).filter(v => v !== null && v !== undefined && v !== ''))]
      .sort((a, b) => String(a).localeCompare(String(b)));
  }

  function value(id) { const el = document.getElementById(id); return el ? el.value.trim() : ''; }

  function build() {
    const d = NG.state.data;
    const parks = d.it_parks || [];
    const companies = d.companies || [];
    const allTech = [...new Set(companies.flatMap(c =>
      Array.isArray(c.tech_stack) ? c.tech_stack : []))].sort();

    document.getElementById('parkFilters').innerHTML =
      '<input id="parkSearch" type="search" placeholder="Search parks…" aria-label="Search parks">' +
      sel('parkCity', 'City filter', unique('city', parks), 'All cities') +
      sel('parkSector', 'Sector filter', unique('sector', parks), 'All sectors') +
      sel('parkCategory', 'Category filter', unique('location_category', parks), 'All categories') +
      sel('parkTier', 'Tier filter', unique('tier', parks), 'All tiers') +
      sel('parkRank', 'Ranking filter', ['Scored', 'Not scored'], 'Any ranking') +
      sel('parkStatus', 'Operational status', unique('operational_status', parks), 'Any status') +
      sel('parkSort', 'Sort parks', ['Name', 'Tier', 'City'], 'Default order');

    document.getElementById('companyFilters').innerHTML =
      '<input id="companySearch" type="search" placeholder="Search companies…" aria-label="Search companies">' +
      selPairs('companyPark', 'Park filter', parks.map(p => [p.park_id, p.park_name]), 'All parks') +
      sel('companySector', 'Sector filter', unique('sector', companies), 'All sectors') +
      sel('companyCategory', 'Category filter', unique('company_category', companies), 'All categories') +
      sel('companyTech', 'Technology filter', allTech, 'All technologies') +
      sel('companyHiring', 'Hiring category', ['Careers link', 'Internship link', 'Direct apply'], 'Any hiring signal') +
      sel('companySort', 'Sort companies', ['Student fit score', 'Name', 'Verification'], 'Default: student fit score');

    document.getElementById('stackFilters').innerHTML =
      sel('stackPreset', 'Quick view', [
        'Java companies', 'Python companies', 'Spring Boot companies', 'React companies',
        'Data engineering companies', 'AI/ML companies', 'Cloud & DevOps companies',
        'Fintech technology companies'
      ], 'All stack views') +
      sel('stackTech', 'Technology', allTech, 'All technologies') +
      sel('stackConfidence', 'Confidence', ['VERIFIED', 'PUBLICLY REPORTED', 'INFERRED', 'UNKNOWN'], 'Any confidence');

    document.getElementById('careerFilters').innerHTML =
      '<input id="careerSearch" type="search" placeholder="Search companies…" aria-label="Search careers">' +
      sel('careerSignal', 'Opportunity type', ['Official careers page', 'Internship page', 'Direct application', '2028 batch eligible'], 'All opportunities');

    const pageKeys = {
      parkSearch: 'parks', parkCity: 'parks', parkSector: 'parks', parkCategory: 'parks',
      parkTier: 'parks', parkRank: 'parks', parkStatus: 'parks', parkSort: 'parks',
      companySearch: 'companies', companyPark: 'companies', companySector: 'companies',
      companyCategory: 'companies', companyTech: 'companies', companyHiring: 'companies',
      companySort: 'companies', stackPreset: 'companies', stackTech: 'companies',
      stackConfidence: 'companies', careerSearch: 'careers', careerSignal: 'careers'
    };
    const on = (id, evt, fn) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener(evt, () => { NG.resetPage(pageKeys[id]); fn(); });
    };
    ['parkSearch', 'companySearch', 'careerSearch'].forEach(id =>
      on(id, 'input', id === 'parkSearch' ? NGParks.render
        : id === 'careerSearch' ? NGCompanies.renderCareers : NGCompanies.render));
    ['parkCity', 'parkSector', 'parkCategory', 'parkTier', 'parkRank', 'parkStatus', 'parkSort'].forEach(id =>
      on(id, 'change', NGParks.render));
    ['companyPark', 'companySector', 'companyCategory', 'companyTech', 'companyHiring', 'companySort'].forEach(id =>
      on(id, 'change', NGCompanies.render));
    ['stackPreset', 'stackTech', 'stackConfidence'].forEach(id =>
      on(id, 'change', NGCompanies.renderTechStacks));
    on('careerSignal', 'change', NGCompanies.renderCareers);
  }

  return { build, value, unique };
})();
