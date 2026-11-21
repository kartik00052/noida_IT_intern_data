window.NGCompanies = (function () {
  const VERIFIED = /^VERIFIED$/i;
  const STACK_PRESETS = {
    'Java companies': ['Java'],
    'Python companies': ['Python'],
    'Spring Boot companies': ['Spring Boot'],
    'React companies': ['React'],
    'Data engineering companies': ['Spark', 'Kafka', 'Airflow', 'SQL'],
    'AI/ML companies': ['PyTorch', 'TensorFlow', 'LLM', 'MLOps'],
    'Cloud & DevOps companies': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform'],
    'Fintech technology companies': []
  };

  function list() {
    const d = NG.state.data;
    const q = NGFilters.value('companySearch').toLowerCase();
    const tech = NGFilters.value('companyTech');
    let items = (d.companies || []).filter(c => {
      const stack = Array.isArray(c.tech_stack) ? c.tech_stack : [];
      return (!q || JSON.stringify(c).toLowerCase().includes(q)) &&
        (!NGFilters.value('companyPark') || c.it_park_id === NGFilters.value('companyPark')) &&
        (!NGFilters.value('companySector') || c.sector === NGFilters.value('companySector')) &&
        (!NGFilters.value('companyCategory') || c.company_category === NGFilters.value('companyCategory')) &&
        (!tech || stack.includes(tech)) &&
        (() => {
          const h = NGFilters.value('companyHiring');
          if (!h) return true;
          if (h === 'Careers link') return !!c.careers_url;
          if (h === 'Internship link') return !!c.internship_url;
          if (h === 'Direct apply') return !!c.direct_application_url;
          return true;
        })();
    });
    const sort = NGFilters.value('companySort');
    const verifiedFirst = (a, b) => {
      const av = VERIFIED.test(String(a.verification_status || '')) ? 0 : 1;
      const bv = VERIFIED.test(String(b.verification_status || '')) ? 0 : 1;
      return av - bv;
    };
    if (sort === 'Name') items.sort((a, b) => a.company_name.localeCompare(b.company_name));
    else if (sort === 'Verification') items.sort((a, b) => verifiedFirst(a, b) || a.company_name.localeCompare(b.company_name));
    else items.sort((a, b) => verifiedFirst(a, b) || (b.student_fit_score || 0) - (a.student_fit_score || 0));
    return items;
  }

  function render() {
    NG.paginate(list(), 'companies', (c) => `<tr>
      <td><strong>${NG.esc(c.company_name)}</strong><br><span class="muted">${NG.esc(c.business_domain || '')}</span></td>
      <td>${NG.esc(c.company_category)}</td>
      <td>${NG.esc(c.it_park_name || 'Not mapped')}</td>
      <td>${NG.esc(c.sector || '—')}</td>
      <td>${NG.stackChips(c.tech_stack, c.tech_stack_confidence)}</td>
      <td>${NG.esc(c.student_fit_score == null ? '—' : c.student_fit_score)}</td>
      <td>${NG.statusBadge(c.verification_status)}</td>
      <td><button class="btn" data-company="${NG.esc(c.company_id)}">Details</button></td>
    </tr>`, document.querySelector('#companyTable tbody'));
  }

  function rolesText(c) {
    if (Array.isArray(c.entry_level_roles)) return c.entry_level_roles.join(', ') || 'No verified opening captured';
    return c.entry_level_roles || 'No verified opening captured';
  }

  function detail(id) {
    const c = (NG.state.data.companies || []).find(x => x.company_id === id);
    if (!c) return;
    const links = [
      ['Official website', c.official_website],
      ['LinkedIn', c.linkedin_url],
      ['Careers', c.careers_url],
      ['Internships', c.internship_url],
      ['Direct application', c.direct_application_url],
      ['Stack evidence', c.technology_evidence_source],
      ['Association evidence', c.tenant_verification_source]
    ].filter(x => x[1]).map(x => NG.link(x[1], x[0])).join(' ');
    NG.openModal(`
      <dl class="kv">
        <dt>Category</dt><dd>${NG.esc(c.company_category)}${c.secondary_categories ? ' / ' + NG.esc(c.secondary_categories) : ''}</dd>
        <dt>Domain</dt><dd>${NG.esc(c.business_domain || 'Unavailable')}</dd>
        <dt>Location</dt><dd>${NG.esc(c.it_park_name || 'Not mapped')}</dd>
        <dt>Noida office status</dt><dd>${NG.esc(c.noida_office_status || 'Unavailable')}</dd>
        <dt>Student fit score</dt><dd>${NG.esc(c.student_fit_score == null ? '—' : c.student_fit_score)} / 100</dd>
        <dt>Stack confidence</dt><dd>${NG.stackChips(c.tech_stack, c.tech_stack_confidence)}</dd>
        <dt>Entry-level roles</dt><dd>${NG.esc(rolesText(c))}</dd>
        <dt>2028 batch eligible</dt><dd>${c.eligible_2028_batch == null ? 'Unknown' : NG.esc(c.eligible_2028_batch)}</dd>
        <dt>Hiring verified</dt><dd>${NG.esc(c.hiring_verified_date || 'Unknown')}</dd>
        <dt>Verification</dt><dd>${NG.statusBadge(c.verification_status)}</dd>
        <dt>Last checked</dt><dd>${NG.esc(c.last_checked || c.last_verified || 'Not checked')}</dd>
      </dl>
      <h3>Links</h3><div class="links">${links || '<span class="muted">No permitted links captured.</span>'}</div>
    `, c.company_name);
  }

  function renderTechStacks() {
    const tech = NGFilters.value('stackTech');
    const conf = NGFilters.value('stackConfidence');
    const preset = NGFilters.value('stackPreset');
    const presetTech = STACK_PRESETS[preset];
    const items = (NG.state.data.companies || []).filter(c => {
      const stack = Array.isArray(c.tech_stack) ? c.tech_stack : [];
      const presetOk = !presetTech || (preset === 'Fintech technology companies'
        ? /fintech|banking technology/i.test(c.company_category || '')
        : presetTech.some(t => stack.includes(t)));
      return presetOk && (!tech || stack.includes(tech)) &&
        (!conf || String(c.tech_stack_confidence || 'UNKNOWN').toUpperCase() === conf);
    });
    document.getElementById('stackResults').innerHTML = items.length ? items.map(c => `
      <div class="card">
        <h4>${NG.esc(c.company_name)}</h4>
        <p>${NG.esc(c.company_category)} &middot; ${NG.esc(c.it_park_name || 'Not mapped')}</p>
        <p>${NG.stackChips(c.tech_stack, c.tech_stack_confidence)}</p>
        <p>Fit score: ${NG.esc(c.student_fit_score == null ? '—' : c.student_fit_score)} &middot; ${NG.statusBadge(c.verification_status)}</p>
        <div class="links">${c.technology_evidence_source ? NG.link(c.technology_evidence_source, 'Stack evidence') : ''}</div>
      </div>`).join('') : '<div class="panel empty">No companies match this technology filter.</div>';
  }

  function renderCareers() {
    const d = NG.state.data;
    const q = NGFilters.value('careerSearch').toLowerCase();
    const sig = NGFilters.value('careerSignal');
    const items = (d.companies || []).filter(c => {
      const okQ = !q || c.company_name.toLowerCase().includes(q);
      if (!okQ) return false;
      if (!sig) return true;
      if (sig === 'Official careers page') return !!c.careers_url;
      if (sig === 'Internship page') return !!c.internship_url;
      if (sig === 'Direct application') return !!c.direct_application_url;
      if (sig === '2028 batch eligible') return c.eligible_2028_batch === true || c.eligible_2028_batch === 'Yes';
      return true;
    });
    NG.paginate(items, 'careers', (c) => `<tr>
      <td><strong>${NG.esc(c.company_name)}</strong></td>
      <td>${NG.link(c.official_website, 'Website')}</td>
      <td>${NG.link(c.careers_url, 'Careers')}</td>
      <td>${NG.link(c.internship_url, 'Internships')}</td>
      <td>${NG.link(c.direct_application_url, 'Apply')}</td>
      <td>${NG.esc(rolesText(c))}</td>
      <td>${c.eligible_2028_batch == null ? 'Unknown' : NG.esc(c.eligible_2028_batch)}</td>
      <td>${NG.esc(c.hiring_verified_date || 'Not verified')}</td>
    </tr>`, document.querySelector('#careerTable tbody'));
  }

  document.addEventListener('click', (e) => {
    const b = e.target.closest?.('[data-company]');
    if (b) detail(b.dataset.company);
  });

  return { render, detail, renderTechStacks, renderCareers };
})();
