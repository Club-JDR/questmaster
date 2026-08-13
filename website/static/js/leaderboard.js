/**
 * Trophy leaderboard page interactions:
 *  - the "Global / Événements" toggle, which swaps between the badge-based
 *    leaderboards and the special-event leaderboard (event picker + results,
 *    both server-rendered already — no lazy fetch, same as the "Par annonce /
 *    Par session" toggle in stats.js). Default pane: "global", unless an
 *    event is already selected (?event=<id> on load), in which case
 *    data-default-mode is "events".
 */
(function () {
  const root = document.querySelector("[data-leaderboard-root]");
  if (!root) return;

  const toggles = root.querySelectorAll("[data-lb-toggle]");
  const panes = root.querySelectorAll("[data-lbpane]");

  function applyMode(mode) {
    panes.forEach(function (el) {
      el.classList.toggle("hidden", el.dataset.lbpane !== mode);
    });
    toggles.forEach(function (t) {
      const on = t.dataset.lbToggle === mode;
      t.classList.toggle("btn-primary", on); // filled = active, plain = inactive
      t.classList.toggle("btn-active", on);
    });
  }

  toggles.forEach(function (t) {
    t.addEventListener("click", function () { applyMode(t.dataset.lbToggle); });
  });

  applyMode(root.dataset.defaultMode || "global");
})();
