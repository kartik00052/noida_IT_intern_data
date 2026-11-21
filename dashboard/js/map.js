window.NGMap = (function () {
  const TIER_COLORS = { A: '#d64545', B: '#e78b2c', C: '#d6c02b', D: '#3d9b68', E: '#6c7bb5' };

  function jitter(id) {
    let h = 0;
    const s = String(id);
    for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
    const angle = (h % 360) * Math.PI / 180;
    const radius = 0.0012 * (0.5 + ((h >>> 9) % 50) / 100);
    return [Math.cos(angle) * radius, Math.sin(angle) * radius];
  }

  function updateNoCoords() {
    const panel = document.getElementById('noCoordsPanel');
    if (!panel) return;
    const missing = (NG.state.data?.it_parks || []).filter(p => p.latitude == null || p.longitude == null);
    if (!missing.length) {
      panel.hidden = true;
      panel.innerHTML = '';
      return;
    }
    panel.innerHTML = '<h3>Parks without coordinates</h3><ul>' +
      missing.map(p => `<li>${NG.esc(p.park_name)}</li>`).join('') + '</ul>';
    panel.hidden = false;
  }

  function unavailable(container) {
    if (container) container.innerHTML = '<div class="map-fallback">Map unavailable (CDN blocked)</div>';
  }

  function init() {
    if (NG.state.map) return;
    const container = document.getElementById('map');
    updateNoCoords();
    if (typeof L === 'undefined') {
      unavailable(container);
      return;
    }
    try {
      const parks = NG.state.data?.it_parks || [];
      const coordCounts = {};
      parks.forEach(p => {
        if (p.latitude == null || p.longitude == null) return;
        const key = p.latitude + ',' + p.longitude;
        coordCounts[key] = (coordCounts[key] || 0) + 1;
      });

      const map = L.map(container, { scrollWheelZoom: false }).setView([28.53, 77.42], 10);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      parks.forEach(p => {
        if (p.latitude == null || p.longitude == null) return;
        const key = p.latitude + ',' + p.longitude;
        const [dx, dy] = coordCounts[key] > 1 ? jitter(p.park_id) : [0, 0];
        const color = TIER_COLORS[p.tier] || TIER_COLORS.E;
        const m = L.circleMarker([p.latitude + dy, p.longitude + dx], {
          radius: 7, color: '#fff', weight: 1.5, fillColor: color, fillOpacity: .92
        }).addTo(map);
        m.bindPopup(`<strong>${NG.esc(p.park_name)}</strong><br>${NG.esc(p.city)} · ${NG.esc(p.sector)}<br>
          Tier ${NG.esc(p.tier)} · ${NG.esc(p.location_category)}<br>
          <span style="font-size:11px">approximate location · unverified</span>`);
        m.on('click', () => NGParks.profile(p.park_id));
        NG.state.markers.push(m);
      });

      const legend = L.control({ position: 'bottomright' });
      legend.onAdd = function () {
        const div = L.DomUtil.create('div', 'map-legend');
        div.innerHTML = Object.entries(TIER_COLORS).map(([tier, c]) =>
          `<div><span class="legend-dot" style="background:${c}"></span>Tier ${tier}</div>`
        ).join('');
        return div;
      };
      legend.addTo(map);
      NG.state.map = map;
    } catch (e) {
      NG.state.map = null;
      unavailable(container);
    }
  }

  function invalidate() {
    if (NG.state.map) setTimeout(() => NG.state.map.invalidateSize(), 80);
  }

  return { init, invalidate };
})();
