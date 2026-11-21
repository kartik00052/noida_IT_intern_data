window.NG = (function () {
  const state = {
    data: null,
    rawFallback: false,
    page: { parks: 1, companies: 1, careers: 1, sources: 1 },
    pageSize: 15,
    map: null,
    markers: []
  };

  const esc = (v) => String(v == null ? '' : v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

  const isUrl = (v) => typeof v === 'string' && /^https?:\/\//i.test(v);

  function link(v, label) {
    if (isUrl(v)) return `<a href="${esc(v)}" target="_blank" rel="noopener noreferrer">${esc(label || 'Open')}</a>`;
    if (typeof v === 'string' && v.trim()) return `<span class="ref-text">Reference (no URL): ${esc(v)}</span>`;
    return '<span class="muted">—</span>';
  }

  function statusBadge(status) {
    const s = String(status || 'Unknown');
    const labels = {
      VERIFIED: 'Verified', OSM_LISTED_UNVERIFIED: 'Unverified',
      UNVERIFIED_CANDIDATE: 'Unverified candidate', SEED_LEAD: 'Seed lead',
      HISTORICAL: 'Historical', INFERRED: 'Inferred', PUBLICLY_REPORTED: 'Publicly reported',
      UNKNOWN: 'Unknown'
    };
    const label = labels[s] || s.replace(/_/g, ' ');
    const cls = /^VERIFIED$/.test(s) ? 'pill-ok'
      : /UNVERIFIED|SEED|HISTORICAL/.test(s) ? 'pill-warn' : 'pill-neutral';
    return `<span class="pill ${cls}">${esc(label)}</span>`;
  }

  function stackChips(list, confidence) {
    const arr = Array.isArray(list) ? list : [];
    if (!arr.length) return '<span class="chip chip-unknown">UNKNOWN</span>';
    const c = String(confidence || 'UNKNOWN').toUpperCase().replace(/_/g, ' ');
    const cls = c === 'VERIFIED' ? 'chip-verified'
      : c === 'PUBLICLY REPORTED' ? 'chip-reported'
      : c === 'INFERRED' ? 'chip-inferred' : 'chip-unknown';
    return arr.map(t => `<span class="chip ${cls}">${esc(t)}</span>`).join('');
  }

  function resetPage(key) {
    if (key && Object.prototype.hasOwnProperty.call(state.page, key)) state.page[key] = 1;
  }

  function paginate(items, key, renderRow, tableBody) {
    const p = state.page[key];
    const pages = Math.max(1, Math.ceil(items.length / state.pageSize));
    state.page[key] = Math.min(p, pages);
    const start = (state.page[key] - 1) * state.pageSize;
    const slice = items.slice(start, start + state.pageSize);
    const table = tableBody.closest('table');
    const colspan = table ? table.querySelectorAll('thead th').length : 1;
    tableBody.innerHTML = slice.length
      ? slice.map(renderRow).join('')
      : `<tr><td colspan="${colspan}" class="empty">No records match the current filters.</td></tr>`;
    const pager = document.getElementById(key + 'Pager');
    if (pager) {
      pager.innerHTML = `
        <button class="btn" data-page-key="${key}" data-page-act="prev" ${state.page[key] === 1 ? 'disabled' : ''}>Previous</button>
        <span>Page ${state.page[key]} of ${pages} &middot; ${items.length} records</span>
        <button class="btn" data-page-key="${key}" data-page-act="next" ${state.page[key] === pages ? 'disabled' : ''}>Next</button>`;
    }
  }

  function bindPagers() {
    document.addEventListener('click', (e) => {
      const b = e.target.closest('[data-page-act]');
      if (!b) return;
      const key = b.getAttribute('data-page-key');
      state.page[key] += b.getAttribute('data-page-act') === 'next' ? 1 : -1;
      const map = { parks: window.NGParks.render, companies: window.NGCompanies.render,
        careers: window.NGCompanies.renderCareers, sources: renderSources };
      if (map[key]) map[key]();
    });
  }

  function normaliseFallback(raw) {
    const companies = (raw.companies || []).map((c, i) => ({
      company_id: c.company_id || `C${i + 1}`,
      company_name: c.company_name,
      company_category: c.company_category || 'IT Services',
      business_domain: null,
      it_park_name: c.park_name || null,
      sector: null,
      tech_stack: c.tech_stack || [],
      tech_stack_confidence: c.tech_confidence || 'UNKNOWN',
      official_website: c.website || null,
      linkedin_url: c.linkedin_url || null,
      careers_url: c.careers_url || null,
      internship_url: null,
      direct_application_url: null,
      entry_level_roles: null,
      eligible_2028_batch: null,
      hiring_verified_date: null,
      technology_evidence_source: c.tech_evidence_url || null,
      tenant_verification_source: c.source || null,
      verification_status: c.verification_status || 'UNKNOWN',
      student_fit_score: 0,
      last_verified: c.last_verified || null
    }));
    return {
      metadata: { research_date: raw.metadata?.generated || null, data_warning:
        'Raw collector fallback in use. Run scripts/build_datasets.py to produce the enriched dataset.' },
      it_parks: [], companies, company_locations: [], sources: []
    };
  }

  async function loadData() {
    const paths = ['../data/NOIDA_GREATER_NOIDA_IT_ECOSYSTEM_2026.json', '../data/noida_it_companies.json'];
    for (let i = 0; i < paths.length; i++) {
      try {
        const res = await fetch(paths[i], { cache: 'no-store' });
        if (!res.ok) continue;
        const json = await res.json();
        state.data = i === 0 ? json : normaliseFallback(json);
        state.rawFallback = i === 1;
        document.getElementById('dataStatus').textContent =
          state.rawFallback ? 'Raw fallback data' : 'Dataset loaded';
        document.getElementById('dataStatus').className = 'pill ' + (state.rawFallback ? 'pill-warn' : 'pill-ok');
        if (state.data.metadata && state.data.metadata.data_warning) {
          const w = document.getElementById('dataWarning');
          w.textContent = state.data.metadata.data_warning;
          w.hidden = false;
        }
        renderAll();
        return;
      } catch (e) { /* try next path */ }
    }
    document.getElementById('dataStatus').textContent = 'Data load failed';
    document.body.insertAdjacentHTML('afterbegin',
      '<div class="alert alert-warn">Could not load the dataset. Serve this folder over HTTP from the project root: <code>python -m http.server 8000</code>.</div>');
  }

  function renderOverview() {
    const d = state.data;
    const c = d.companies || [];
    const p = d.it_parks || [];
    const count = (fn) => c.filter(fn).length;
    const cat = (name) => count(x => String(x.company_category || '').toLowerCase() === name.toLowerCase());
    const cards = [
      ['Total parks', p.length],
      ['Verified parks', p.filter(x => /^VERIFIED$/i.test(String(x.verification_status || ''))).length],
      ['Unique companies', c.length],
      ['MNCs', cat('MNC')],
      ['Product companies', cat('Product-Based')],
      ['Fintechs', cat('Fintech') + cat('Banking Technology')],
      ['IT services companies', cat('IT Services')],
      ['GCCs', cat('GCC')],
      ['Verified stack evidence', count(x =>
        String(x.tech_stack_confidence || '').toUpperCase() === 'VERIFIED')],
      ['Public stack evidence', count(x =>
        String(x.tech_stack_confidence || '').toUpperCase() === 'PUBLICLY REPORTED')],
      ['Company-location links', (d.company_locations || []).length]
    ];
    document.getElementById('statGrid').innerHTML = cards.map(([label, value]) =>
      `<div class="stat"><div class="value">${esc(value)}</div><div class="label">${esc(label)}</div></div>`
    ).join('');
  }

  function renderSources() {
    const d = state.data;
    const q = (document.getElementById('sourceSearch')?.value || '').toLowerCase();
    const items = (d.sources || []).filter(s =>
      !q || JSON.stringify(s).toLowerCase().includes(q));
    paginate(items, 'sources', (s) => `<tr>
      <td>${esc(s.supports)}</td><td>${esc(s.source_title)}</td><td>${esc(s.source_type)}</td>
      <td>${esc(s.evidence_statement)}</td><td>${statusBadge(s.confidence_level)}</td>
      <td>${link(s.source_url, 'Evidence')}</td></tr>`,
      document.querySelector('#sourceTable tbody'));
  }

  function buildSourceFilters() {
    document.getElementById('sourceFilters').innerHTML =
      '<input id="sourceSearch" type="search" placeholder="Search sources…" aria-label="Search sources">';
    document.getElementById('sourceSearch').addEventListener('input', () => {
      resetPage('sources');
      renderSources();
    });
  }

  let lastFocused = null;

  function openModal(html, title) {
    lastFocused = document.activeElement;
    document.getElementById('modalBody').innerHTML =
      `<h2 id="modalTitle">${esc(title)}</h2>` + html;
    document.getElementById('modalBackdrop').hidden = false;
    (document.getElementById('modalClose') || document.querySelector('.modal'))?.focus();
  }

  function closeModal() {
    document.getElementById('modalBackdrop').hidden = true;
    if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
    lastFocused = null;
  }

  function activateTab(tab) {
    document.querySelectorAll('.tab').forEach(t => {
      const active = t === tab;
      t.classList.toggle('active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    document.querySelectorAll('.section').forEach(s =>
      s.classList.toggle('active', s.id === 'section-' + tab.dataset.section));
    if (tab.dataset.section === 'map' && window.NGMap) window.NGMap.invalidate();
  }

  function applyTheme(dark) {
    document.body.classList.toggle('dark', dark);
    document.getElementById('themeToggle').setAttribute('aria-pressed', dark ? 'true' : 'false');
    try { localStorage.setItem('ng-dark', dark ? '1' : '0'); } catch (e) {}
  }

  function bindShell() {
    const tabs = [...document.querySelectorAll('.tab')];
    tabs.forEach(tab => tab.addEventListener('click', () => activateTab(tab)));
    document.querySelector('.tabs')?.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      e.preventDefault();
      const step = e.key === 'ArrowRight' ? 1 : tabs.length - 1;
      const next = tabs[(i + step) % tabs.length];
      next.focus();
      activateTab(next);
    });
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalBackdrop').addEventListener('click', (e) => {
      if (e.target.id === 'modalBackdrop') closeModal();
    });
    document.addEventListener('keydown', (e) => {
      const backdrop = document.getElementById('modalBackdrop');
      if (e.key === 'Escape') {
        if (!backdrop.hidden) closeModal();
        return;
      }
      if (e.key !== 'Tab' || backdrop.hidden) return;
      const focusables = [...backdrop.querySelectorAll('button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])')];
      const first = focusables[0], last = focusables[focusables.length - 1];
      if (!first) { e.preventDefault(); backdrop.querySelector('.modal').focus(); return; }
      if (e.shiftKey && (document.activeElement === first || !backdrop.contains(document.activeElement))) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && (document.activeElement === last || !backdrop.contains(document.activeElement))) {
        e.preventDefault(); first.focus();
      }
    });
    document.getElementById('themeToggle').addEventListener('click', () => {
      applyTheme(!document.body.classList.contains('dark'));
    });
    let savedTheme = null;
    try { savedTheme = localStorage.getItem('ng-dark'); } catch (e) {}
    applyTheme(savedTheme === '1');
    bindPagers();
  }

  function showFileNotice() {
    if (location.protocol !== 'file:') return;
    const main = document.querySelector('main');
    if (!main || main.querySelector('.file-notice')) return;
    main.insertAdjacentHTML('afterbegin',
      '<div class="notice file-notice">Opened via <code>file://</code> — data fetching is blocked here. Run <code>python -m http.server 8000</code> from the project root and open the served page.</div>');
  }

  function renderAll() {
    renderOverview();
    window.NGFilters.build();
    window.NGParks.render();
    window.NGCompanies.render();
    window.NGCompanies.renderTechStacks();
    window.NGCompanies.renderCareers();
    renderSources();
    try {
      window.NGMap.init();
    } catch (e) {
      const mapEl = document.getElementById('map');
      if (mapEl) mapEl.innerHTML = '<div class="map-fallback">Map unavailable (CDN blocked)</div>';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    showFileNotice();
    bindShell();
    buildSourceFilters();
    loadData();
  });

  return { state, esc, isUrl, link, statusBadge, stackChips, paginate, resetPage, openModal, closeModal,
    renderAll, renderSources, renderOverview };
})();
