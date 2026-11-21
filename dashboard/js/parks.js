window.NGParks = (function () {
  const byPark = () => {
    const d = NG.state.data;
    const map = {};
    (d.company_locations || []).forEach(l => {
      if (!l.park_id) return;
      (map[l.park_id] = map[l.park_id] || []).push(l);
    });
    if (!Object.keys(map).length) {
      (d.companies || []).forEach(c => {
        if (!c.it_park_id) return;
        (map[c.it_park_id] = map[c.it_park_id] || []).push(c);
      });
    }
    return map;
  };

  function render() {
    const d = NG.state.data;
    const links = byPark();
    const q = NGFilters.value('parkSearch').toLowerCase();
    let items = (d.it_parks || []).filter(p =>
      (!q || JSON.stringify(p).toLowerCase().includes(q)) &&
      (!NGFilters.value('parkCity') || p.city === NGFilters.value('parkCity')) &&
      (!NGFilters.value('parkCategory') || p.location_category === NGFilters.value('parkCategory')) &&
      (!NGFilters.value('parkTier') || p.tier === NGFilters.value('parkTier')) &&
      (!NGFilters.value('parkStatus') || String(p.operational_status || 'Unknown') === NGFilters.value('parkStatus'))
    );
    const sort = NGFilters.value('parkSort');
    if (sort === 'Name') items = items.slice().sort((a, b) => a.park_name.localeCompare(b.park_name));
    if (sort === 'Tier') items = items.slice().sort((a, b) => String(a.tier).localeCompare(String(b.tier)));
    if (sort === 'City') items = items.slice().sort((a, b) => String(a.city).localeCompare(String(b.city)));

    NG.paginate(items, 'parks', (p) => {
      const count = (links[p.park_id] || []).length;
      return `<tr>
        <td><strong>${NG.esc(p.park_name)}</strong><br><span class="muted">${NG.esc(p.location_category)}</span></td>
        <td>${NG.esc(p.city)}</td><td>${NG.esc(p.sector)}</td>
        <td>${NG.esc(p.location_category)}</td><td>Tier ${NG.esc(p.tier)}</td>
        <td>${p.ranking_score == null ? '<span class="muted">Not scored</span>' : NG.esc(p.ranking_score)}</td>
        <td>${count}</td>
        <td>${NG.statusBadge(p.verification_status)}</td>
        <td><button class="btn" data-park="${NG.esc(p.park_id)}">Profile</button></td>
      </tr>`;
    }, document.querySelector('#parkTable tbody'));
  }

  function profile(id) {
    const d = NG.state.data;
    const p = (d.it_parks || []).find(x => x.park_id === id);
    if (!p) return;
    const rows = (d.company_locations || []).filter(l => l.park_id === id);
    const companies = rows.length
      ? rows.map(l => (d.companies || []).find(c => c.company_id === l.company_id)).filter(Boolean)
      : (d.companies || []).filter(c => c.it_park_id === p.park_id);
    const names = [...new Set(companies.map(c => c.company_name))];
    const techs = [...new Set(companies.flatMap(c => Array.isArray(c.tech_stack) ? c.tech_stack : []))];
    const companyHtml = names.length
      ? names.map(n => `<li>${NG.esc(n)}</li>`).join('') : '<li class="muted">No linked companies in this build.</li>';
    const opp = companies.filter(c => c.careers_url || c.internship_url || c.direct_application_url).length;
    const evidence = (p.source_urls || []).map(u => NG.link(u, 'Location evidence')).join(' ') || '<span class="muted">None captured</span>';
    NG.openModal(`
      <dl class="kv">
        <dt>City / area</dt><dd>${NG.esc(p.city)} &middot; ${NG.esc(p.sector)}</dd>
        <dt>Category</dt><dd>${NG.esc(p.location_category)}</dd>
        <dt>Tier</dt><dd>Tier ${NG.esc(p.tier)} (provisional)</dd>
        <dt>Rank score</dt><dd>${p.ranking_score == null ? 'Not scored — insufficient verified evidence' : NG.esc(p.ranking_score)}</dd>
        <dt>Operational status</dt><dd>${NG.esc(p.operational_status || 'Unknown')}</dd>
        <dt>Verification</dt><dd>${NG.statusBadge(p.verification_status)}</dd>
        <dt>Coordinates</dt><dd>${p.latitude != null ? NG.esc(p.latitude + ', ' + p.longitude) + ' (approximate)' : 'Unavailable'}</dd>
        <dt>Last checked</dt><dd>${NG.esc(p.last_checked || p.last_verified || 'Not checked')}</dd>
      </dl>
      <h3>Companies linked to this location</h3><ul>${companyHtml}</ul>
      <h3>Top technologies</h3><p>${techs.length ? techs.map(t => `<span class="chip chip-unknown">${NG.esc(t)}</span>`).join('') : '<span class="muted">None captured</span>'}</p>
      <h3>Opportunities</h3><p class="muted">${opp} linked company record(s) with a careers, internship or application link.</p>
      <h3>Evidence</h3><div class="links">${evidence}</div>
      <p class="muted">${NG.esc(p.ranking_explanation || '')}</p>
    `, p.park_name);
  }

  document.addEventListener('click', (e) => {
    const b = e.target.closest?.('[data-park]');
    if (b) profile(b.dataset.park);
  });

  return { render, profile, byPark };
})();
