/**
 * App-wide statistics page interactions:
 *  - the "Par session / Par annonce" toggle, which swaps ONLY the donuts and
 *    the activity-rhythm bars (the top 10s and the restriction pie are fixed);
 *  - the top-10 type select, which switches between all games / one-shots /
 *    campaigns.
 *
 * Mirrors the per-user toggle in dashboard.js (initStats) but operates on the
 * already-rendered [data-stats-root] container (no lazy fetch). Chart markup
 * comes from the shared _stats_charts.j2 macros. Default basis: "parties".
 */
(function () {
  const root = document.querySelector("[data-stats-root]");
  if (!root) return;

  // --- Sessions / annonces toggle (donuts + rhythm only) ---
  const donuts = root.querySelectorAll("[data-donut]");
  const toggles = root.querySelectorAll("[data-stat-toggle]");
  const panes = root.querySelectorAll("[data-statpane]");

  function applyBasis(mode) {
    panes.forEach(function (el) {
      el.classList.toggle("hidden", el.dataset.statpane !== mode);
    });
    donuts.forEach(function (el) {
      const pct = parseInt(el.dataset[mode], 10);
      const a = el.dataset.acolor, b = el.dataset.bcolor;
      const ring = el.querySelector("[data-ring]");
      ring.style.background =
        "conic-gradient(" + a + " 0 " + pct + "%, " + b + " " + pct + "% 100%)";
      ring.setAttribute("role", "img");
      ring.setAttribute(
        "aria-label",
        el.dataset.a + " " + pct + "%, " + el.dataset.b + " " + (100 - pct) + "%"
      );
      el.querySelector("[data-apct]").textContent = pct + "%";
      el.querySelector("[data-bpct]").textContent = 100 - pct + "%";
    });
    toggles.forEach(function (t) {
      const on = t.dataset.statToggle === mode;
      t.classList.toggle("btn-primary", on); // filled = active, plain = inactive
      t.classList.toggle("btn-active", on);
    });
  }

  toggles.forEach(function (t) {
    t.addEventListener("click", function () { applyBasis(t.dataset.statToggle); });
  });
  applyBasis("parties");

  // --- Top 10 type select (all / oneshot / campaign) ---
  const select = root.querySelector("[data-top-type-select]");
  const groups = root.querySelectorAll("[data-topgroup]");
  if (select) {
    select.addEventListener("change", function () {
      groups.forEach(function (g) {
        g.classList.toggle("hidden", g.dataset.topgroup !== select.value);
      });
    });
  }
})();
