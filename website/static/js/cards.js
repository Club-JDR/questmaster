/** @type {HTMLElement | null} */
let _staleToast = null;
/** @type {string | null} */
let _lastHtml = null;

function refreshCards() {
  const params = new URLSearchParams(globalThis.location.search);
  const container = document.getElementById("game-cards-container");
  if (!container) return;

  fetch(`/annonces/cards/?${params.toString()}`)
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.text();
    })
    .then(function (html) {
      if (_staleToast) { _staleToast.remove(); _staleToast = null; }

      const prev = _lastHtml;
      _lastHtml = html;

      // Skip when content hasn't changed since last fetch
      if (prev !== null && prev === html) return;

      if (globalThis.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        container.innerHTML = html;
        return;
      }

      // Fade out (skeletons or stale cards) → swap → fade in
      container.style.transition = "opacity 0.2s ease";
      container.getBoundingClientRect(); // force reflow to commit transition start state
      container.style.opacity = "0";
      container.addEventListener(
        "transitionend",
        function () {
          container.innerHTML = html;
          container.offsetHeight; // force reflow before fade-in
          container.style.opacity = "1";
        },
        { once: true }
      );
    })
    .catch(function () {
      if (!_staleToast) {
        _staleToast = document.createElement("div");
        _staleToast.className = "toast toast-end toast-bottom z-50";
        _staleToast.innerHTML =
          '<div class="alert alert-warning shadow-lg py-2 px-3 text-sm gap-2">' +
          '<i class="ph ph-wifi-slash"></i>' +
          "<span>Connexion perdue — données figées</span>" +
          "</div>";
        document.body.appendChild(_staleToast);
      }
    });
}

refreshCards(); // Replace skeleton cards as soon as the script loads
setInterval(refreshCards, 10000);