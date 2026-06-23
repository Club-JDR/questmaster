/**
 * Dashboard panels: lazy-load the agenda + stats fragment (heavy queries) and
 * wire the per-session / per-annonce ratio toggle.
 *
 * The fragment is fetched from the URL in #dashboard-panels[data-src]; when no
 * data-src is present (demo page) the panels are already inline and only the
 * toggle is initialised.
 */
(function () {
  /** Wire the Sessions/Annonces toggle for donuts, rhythm bars and top lists. */
  function initStats(root) {
    const donuts = root.querySelectorAll("[data-donut]");
    const toggles = root.querySelectorAll("[data-stat-toggle]");
    const panes = root.querySelectorAll("[data-statpane]");
    if (!donuts.length) return;

    function apply(mode) {
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
        t.classList.toggle("btn-active", t.dataset.statToggle === mode);
      });
    }

    toggles.forEach(function (t) {
      t.addEventListener("click", function () { apply(t.dataset.statToggle); });
    });
    apply("sessions");
  }

  const panels = document.getElementById("dashboard-panels");
  if (!panels) return;

  const src = panels.dataset.src;
  if (!src) {
    initStats(panels); // already rendered inline (demo)
    return;
  }

  fetch(src)
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.text();
    })
    .then(function (html) {
      panels.innerHTML = html;
      initStats(panels);
    })
    .catch(function () {
      panels.innerHTML =
        '<div role="alert" class="alert alert-warning">' +
        '<i class="ph ph-warning"></i>' +
        "<span>Impossible de charger vos statistiques pour le moment.</span></div>";
    });
})();
