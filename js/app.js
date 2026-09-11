/* 5 West Knowledge Hub — static site app
   No build step, no framework: fetch data/cards.json once, route on
   location.hash, render client-side. */

(() => {
  "use strict";

  const RECENT_KEY = "5west.recentlyViewed";
  const RECENT_MAX = 8;

  let DATA = null;          // { cardTypes, acuities, cards }
  let CARDS_BY_SLUG = null; // Map slug -> card

  const state = {
    query: "",
    types: new Set(),
    acuities: new Set(),
    systems: new Set(),
  };

  const appEl = document.getElementById("app");
  const searchInput = document.getElementById("global-search");
  const searchClear = document.getElementById("global-search-clear");

  // ---------- utilities ----------

  function esc(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function typeInfo(code) {
    return DATA.cardTypes.find((t) => t.code === code) || { label: code, color: "#757575" };
  }

  function acuityInfo(code) {
    return DATA.acuities.find((a) => a.code === code) || { label: code, code };
  }

  function acuityIcon(code) {
    if (code === "emergent") {
      return '<svg class="acuity-icon" viewBox="0 0 16 16"><path d="M8 1.5 15 14H1L8 1.5Z" fill="currentColor"/></svg>';
    }
    if (code === "urgent") {
      return '<svg class="acuity-icon" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6.4" fill="currentColor"/><path d="M8 4.4V8l2.6 1.6" stroke="#fff" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg>';
    }
    return '<svg class="acuity-icon" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>';
  }

  function acuityMark(code) {
    const info = acuityInfo(code);
    return `<span class="acuity-mark ${esc(code)}">${acuityIcon(code)}${esc(info.label)}</span>`;
  }

  function getRecent() {
    try {
      const raw = localStorage.getItem(RECENT_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function pushRecent(slug) {
    try {
      let list = getRecent().filter((s) => s !== slug);
      list.unshift(slug);
      list = list.slice(0, RECENT_MAX);
      localStorage.setItem(RECENT_KEY, JSON.stringify(list));
    } catch (e) {
      /* localStorage unavailable -- fine, recents just won't persist */
    }
  }

  // ---------- data loading ----------

  async function loadData() {
    const res = await fetch("data/cards.json");
    DATA = await res.json();
    CARDS_BY_SLUG = new Map(DATA.cards.map((c) => [c.slug, c]));
  }

  // ---------- search + filter ----------

  function matchesQuery(card, q) {
    if (!q) return true;
    const hay = [
      card.title,
      card.quickAnswer,
      ...(card.condition || []),
      ...(card.procedure || []),
      ...(card.keywords || []),
    ]
      .filter(Boolean)
      .join(" ␟ ")
      .toLowerCase();
    return hay.includes(q);
  }

  function filteredCards() {
    const q = state.query.trim().toLowerCase();
    return DATA.cards.filter((c) => {
      if (!matchesQuery(c, q)) return false;
      if (state.types.size && !state.types.has(c.type)) return false;
      if (state.acuities.size && !state.acuities.has(c.acuity)) return false;
      if (state.systems.size) {
        const cardSystems = new Set(c.system || []);
        let hit = false;
        for (const s of state.systems) if (cardSystems.has(s)) { hit = true; break; }
        if (!hit) return false;
      }
      return true;
    });
  }

  // counts a facet dimension against every OTHER active filter + the search
  // query, but not its own dimension -- lets you multi-select within one
  // facet group instead of the first click zeroing out its own siblings
  function facetCounts(dimension) {
    const q = state.query.trim().toLowerCase();
    const counts = new Map();
    for (const c of DATA.cards) {
      if (!matchesQuery(c, q)) continue;
      if (dimension !== "types" && state.types.size && !state.types.has(c.type)) continue;
      if (dimension !== "acuities" && state.acuities.size && !state.acuities.has(c.acuity)) continue;
      if (dimension !== "systems" && state.systems.size) {
        const cardSystems = new Set(c.system || []);
        let hit = false;
        for (const s of state.systems) if (cardSystems.has(s)) { hit = true; break; }
        if (!hit) continue;
      }
      if (dimension === "types") {
        counts.set(c.type, (counts.get(c.type) || 0) + 1);
      } else if (dimension === "acuities") {
        counts.set(c.acuity, (counts.get(c.acuity) || 0) + 1);
      } else if (dimension === "systems") {
        for (const s of c.system || []) counts.set(s, (counts.get(s) || 0) + 1);
      }
    }
    return counts;
  }

  // ---------- rendering: library ----------

  function renderLibrary() {
    const results = filteredCards();
    const typeCounts = facetCounts("types");
    const acuityCounts = facetCounts("acuities");
    const systemCounts = facetCounts("systems");

    const allSystems = new Set();
    DATA.cards.forEach((c) => (c.system || []).forEach((s) => allSystems.add(s)));
    const systemList = [...allSystems].sort();

    const hasActiveFilters = state.types.size || state.acuities.size || state.systems.size || state.query;

    const recent = getRecent().map((slug) => CARDS_BY_SLUG.get(slug)).filter(Boolean);

    appEl.innerHTML = `
      ${recent.length ? `
        <div class="recent-strip">
          <h3>Recently viewed</h3>
          <div class="recent-chips">
            ${recent.map((c) => `
              <a class="recent-chip" href="#/card/${esc(c.slug)}">
                <span class="dot" style="background:${esc(typeInfo(c.type).color)}"></span>
                ${esc(c.title)}
              </a>
            `).join("")}
          </div>
        </div>
      ` : ""}

      <div class="library-layout">
        <aside class="facets">
          ${hasActiveFilters ? `<button class="clear-filters-btn" id="clear-filters">Clear filters</button>` : ""}

          <div class="facet-group">
            <h3>Type</h3>
            <div class="facet-list">
              ${DATA.cardTypes.map((t) => {
                const count = typeCounts.get(t.code) || 0;
                const active = state.types.has(t.code);
                return `
                  <div class="facet-row ${active ? "active" : ""}" data-dim="types" data-value="${esc(t.code)}" data-zero="${count === 0 && !active}">
                    <span class="facet-dot" style="background:${esc(t.color)}"></span>
                    <span class="facet-name">${esc(t.label)}</span>
                    <span class="facet-count">${count}</span>
                  </div>`;
              }).join("")}
            </div>
          </div>

          <div class="facet-group">
            <h3>Acuity</h3>
            <div class="facet-list">
              ${DATA.acuities.map((a) => {
                const count = acuityCounts.get(a.code) || 0;
                const active = state.acuities.has(a.code);
                return `
                  <div class="facet-row ${active ? "active" : ""}" data-dim="acuities" data-value="${esc(a.code)}" data-zero="${count === 0 && !active}">
                    ${acuityIcon(a.code)}
                    <span class="facet-name">${esc(a.label)}</span>
                    <span class="facet-count">${count}</span>
                  </div>`;
              }).join("")}
            </div>
          </div>

          <div class="facet-group">
            <h3>System</h3>
            <div class="facet-list">
              ${systemList.map((s) => {
                const count = systemCounts.get(s) || 0;
                const active = state.systems.has(s);
                return `
                  <div class="facet-row ${active ? "active" : ""}" data-dim="systems" data-value="${esc(s)}" data-zero="${count === 0 && !active}">
                    <span class="facet-name">${esc(s)}</span>
                    <span class="facet-count">${count}</span>
                  </div>`;
              }).join("")}
            </div>
          </div>
        </aside>

        <div class="results">
          <div class="results-head">
            <div class="results-count"><strong>${results.length}</strong> of ${DATA.cards.length} cards</div>
          </div>
          <div class="card-grid">
            ${results.length ? results.map(renderCardTile).join("") : `
              <div class="empty-state">
                <p>No cards match${state.query ? ` "${esc(state.query)}"` : ""}${hasActiveFilters ? " with the current filters" : ""}.</p>
                ${hasActiveFilters ? `<button class="clear-filters-btn" id="clear-filters-empty">Clear filters</button>` : ""}
              </div>`}
          </div>
        </div>
      </div>
    `;

    appEl.querySelectorAll("[data-dim]").forEach((row) => {
      row.addEventListener("click", () => {
        const dim = row.dataset.dim;
        const value = row.dataset.value;
        const set = state[dim];
        if (set.has(value)) set.delete(value); else set.add(value);
        renderLibrary();
      });
    });
    const clearBtn = document.getElementById("clear-filters") || document.getElementById("clear-filters-empty");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        state.types.clear();
        state.acuities.clear();
        state.systems.clear();
        state.query = "";
        searchInput.value = "";
        toggleSearchClear();
        renderLibrary();
      });
    }
  }

  function renderCardTile(c) {
    const t = typeInfo(c.type);
    const reviewedLabel = c.lastReviewed ? new Date(c.lastReviewed).toLocaleDateString("en-US", { month: "short", year: "numeric" }) : null;
    return `
      <a class="card-tile" href="#/card/${esc(c.slug)}">
        <div class="card-tile-top">
          <span class="type-pill" style="background:${esc(t.color)}">${esc(t.label)}</span>
          ${acuityMark(c.acuity)}
        </div>
        <h3 class="card-title">${esc(c.title)}</h3>
        ${c.system && c.system.length ? `<div class="card-system-label">${esc(c.system.join(" · "))}</div>` : ""}
        <div class="card-quick-answer">${esc(c.quickAnswer || "")}</div>
        <div class="card-tile-bottom">
          <span>${c.version ? "v" + esc(c.version) : ""}</span>
          <span>${reviewedLabel ? "Reviewed " + esc(reviewedLabel) : ""}</span>
        </div>
      </a>
    `;
  }

  // ---------- rendering: card detail ----------

  function renderCardDetail(slug) {
    const c = CARDS_BY_SLUG.get(slug);
    if (!c) {
      appEl.innerHTML = `
        <div class="empty-state">
          <p>That card isn't in the Hub.</p>
          <a class="clear-filters-btn" href="#/">Back to Library</a>
        </div>`;
      return;
    }

    pushRecent(slug);
    const t = typeInfo(c.type);
    const reviewedLabel = c.lastReviewed ? new Date(c.lastReviewed).toLocaleDateString("en-US", { month: "short", year: "numeric" }) : null;

    const jumpItems = c.sections.map((s) => {
      const cls = s.level >= 3 ? "rail-item sub" : "rail-item";
      return `<a class="${cls}" href="#/card/${esc(slug)}/section/${esc(s.secCode)}">${esc(s.heading)}</a>`;
    }).join("");

    const refItems = (c.references || []).map((r) => `
      <div class="rail-ref">
        ${r.type ? `<span class="ref-type">${esc(r.type)}</span><br>` : ""}
        ${esc(r.citation)}
      </div>
    `).join("") || `<div class="rail-empty">No references logged for this card.</div>`;

    const relatedItems = (c.related || []).map((r) => {
      const target = CARDS_BY_SLUG.get(r.targetSlug);
      if (!target) return "";
      const tt = typeInfo(target.type);
      return `
        <a class="rail-related-item" href="#/card/${esc(target.slug)}">
          <span class="dot" style="width:7px;height:7px;border-radius:50%;background:${esc(tt.color)};flex-shrink:0"></span>
          ${esc(target.title)}
        </a>`;
    }).join("") || `<div class="rail-empty">No related cards linked.</div>`;

    appEl.innerHTML = `
      <a class="back-to-library" href="#/">&larr; Back to Library</a>
      <nav class="crumb-bar">
        <a href="#/">Library</a>
        <span class="crumb-sep">›</span>
        <a href="#/?type=${esc(c.type)}">${esc(t.label)}</a>
        <span class="crumb-sep">›</span>
        <span class="crumb-current">${esc(c.title)}</span>
      </nav>

      <div class="detail-layout">
        <div class="detail-main">
          <div class="detail-head">
            <div class="detail-head-top">
              <span class="type-pill" style="background:${esc(t.color)}">${esc(t.label)}</span>
              ${acuityMark(c.acuity)}
            </div>
            <h1 class="detail-title">${esc(c.title)}</h1>
            <div class="detail-meta">
              ${c.version ? `<span><strong>v${esc(c.version)}</strong></span>` : ""}
              ${reviewedLabel ? `<span>Reviewed <strong>${esc(reviewedLabel)}</strong></span>` : `<span>Not yet SME-reviewed</span>`}
              ${c.system && c.system.length ? `<span>${esc(c.system.join(" · "))}</span>` : ""}
            </div>
            ${c.quickAnswerHtml ? `
              <div class="qa-callout">
                <span class="qa-label">Quick Answer</span>
                <div class="qa-callout-body">${c.quickAnswerHtml}</div>
              </div>
            ` : ""}
          </div>

          <div class="sections">
            ${c.sections.map((s, i) => renderSection(s, i === 0)).join("")}
          </div>

          ${c.sourcePrecedence ? `
            <div class="section-block open" data-level="2">
              <div class="section-toggle" style="cursor:default">Source precedence</div>
              <div class="section-body" style="display:block;padding-top:0">${esc(c.sourcePrecedence)}</div>
            </div>
          ` : ""}
        </div>

        <aside class="rail">
          <div class="rail-box open">
            <button class="rail-toggle" data-rail-toggle>On this card <svg class="section-chevron" viewBox="0 0 8 12"><path d="M1 1l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
            <div class="rail-list">${jumpItems}</div>
          </div>
          <div class="rail-box">
            <button class="rail-toggle" data-rail-toggle>References (${(c.references || []).length}) <svg class="section-chevron" viewBox="0 0 8 12"><path d="M1 1l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
            <div class="rail-list">${refItems}</div>
          </div>
          <div class="rail-box">
            <button class="rail-toggle" data-rail-toggle>Related cards (${(c.related || []).length}) <svg class="section-chevron" viewBox="0 0 8 12"><path d="M1 1l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
            <div class="rail-list">${relatedItems}</div>
          </div>
        </aside>
      </div>
    `;

    appEl.querySelectorAll("[data-rail-toggle]").forEach((btn) => {
      btn.addEventListener("click", () => btn.closest(".rail-box").classList.toggle("open"));
    });
    appEl.querySelectorAll(".section-toggle[data-section-toggle]").forEach((btn) => {
      btn.addEventListener("click", () => btn.closest(".section-block").classList.toggle("open"));
    });
  }

  function renderSection(s, isFirst) {
    // collapsible flag from the data, but always force the first section
    // open on arrival so a card never opens as a wall of chevrons
    const startOpen = isFirst || !s.collapsible;
    return `
      <div class="section-block ${startOpen ? "open" : ""}" data-level="${s.level}" id="sec-${esc(s.secCode)}">
        <button class="section-toggle" data-section-toggle>
          <svg class="section-chevron" viewBox="0 0 8 12"><path d="M1 1l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          ${esc(s.heading)}
        </button>
        <div class="section-body">${s.bodyHtml}</div>
      </div>
    `;
  }

  // ---------- routing ----------

  function parseHash() {
    const hash = location.hash.replace(/^#/, "") || "/";
    const [path, queryStr] = hash.split("?");
    const params = new URLSearchParams(queryStr || "");
    return { path, params };
  }

  function applyQueryParams(params) {
    state.types.clear();
    state.acuities.clear();
    state.systems.clear();
    if (params.get("type")) state.types.add(params.get("type"));
    if (params.get("acuity")) state.acuities.add(params.get("acuity"));
    if (params.get("system")) state.systems.add(params.get("system"));
  }

  function route() {
    const { path, params } = parseHash();
    const cardMatch = path.match(/^\/card\/([^/]+)(?:\/section\/([^/]+))?$/);

    if (cardMatch) {
      renderCardDetail(decodeURIComponent(cardMatch[1]));
      if (cardMatch[2]) {
        requestAnimationFrame(() => {
          const el = document.getElementById(`sec-${cardMatch[2]}`);
          if (el) {
            el.classList.add("open");
            el.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        });
      } else {
        window.scrollTo(0, 0);
      }
      return;
    }

    applyQueryParams(params);
    renderLibrary();
    window.scrollTo(0, 0);
  }

  // ---------- search box wiring ----------

  function toggleSearchClear() {
    searchClear.hidden = !searchInput.value;
  }

  searchInput.addEventListener("input", () => {
    state.query = searchInput.value;
    toggleSearchClear();
    if (parseHash().path === "/") renderLibrary();
  });
  searchClear.addEventListener("click", () => {
    searchInput.value = "";
    state.query = "";
    toggleSearchClear();
    searchInput.focus();
    if (parseHash().path === "/") renderLibrary();
    else location.hash = "#/";
  });

  window.addEventListener("hashchange", route);

  // ---------- boot ----------

  loadData()
    .then(route)
    .catch((err) => {
      appEl.innerHTML = `<div class="empty-state"><p>Couldn't load the card data (${esc(err.message)}). Try refreshing.</p></div>`;
      console.error(err);
    });
})();
