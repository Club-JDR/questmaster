/** @type {HTMLElement | null} */
let _staleToast = null;
/** @type {string | null} */
let _lastHtml = null;
let _hintShown = false;
let _scrollListenerActive = false;

/**
 * @param {HTMLElement} container
 * @param {HTMLElement} indicator
 */
function syncActiveDot(container, indicator) {
  const first = /** @type {HTMLElement | null} */ (container.firstElementChild);
  if (!first) return;
  const cardWidth = first.offsetWidth;
  const gap = 12; // gap-3 = 12px
  const index = Math.min(
    Math.round(container.scrollLeft / (cardWidth + gap)),
    indicator.children.length - 1
  );
  Array.from(indicator.children).forEach(function (dot, i) {
    dot.classList.toggle("active", i === index);
  });
}

function buildCarouselDots() {
  const container = document.getElementById("game-cards-container");
  const indicator = document.getElementById("carousel-indicator");
  if (!container || !indicator) return;

  if (globalThis.innerWidth >= 640) {
    indicator.innerHTML = "";
    return;
  }

  const count = container.children.length;
  if (count <= 1) {
    indicator.innerHTML = "";
    return;
  }

  indicator.innerHTML = Array.from({ length: count }, function () {
    return "<div></div>";
  }).join("");

  if (!_scrollListenerActive) {
    _scrollListenerActive = true;
    container.addEventListener(
      "scroll",
      function () { syncActiveDot(container, indicator); },
      { passive: true }
    );
  }

  syncActiveDot(container, indicator);
}

/** @param {HTMLElement} container */
function maybeShowSwipeHint(container) {
  if (_hintShown) return;
  if (globalThis.innerWidth >= 640) return;
  if (localStorage.getItem("qm_swipe_hinted")) return;
  if (!container || container.children.length <= 1) return;

  _hintShown = true;

  if (globalThis.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    localStorage.setItem("qm_swipe_hinted", "1");
    return;
  }

  setTimeout(function () {
    container.scrollBy({ left: 70, behavior: "smooth" });
    setTimeout(function () {
      container.scrollBy({ left: -70, behavior: "smooth" });
      localStorage.setItem("qm_swipe_hinted", "1");
    }, 650);
  }, 900);
}

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
        buildCarouselDots();
        maybeShowSwipeHint(container);
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
          container.getBoundingClientRect(); // force reflow before fade-in
          container.style.opacity = "1";
          buildCarouselDots();
          maybeShowSwipeHint(container);
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

if (location.pathname === "/annonces/" || location.pathname === "/") {
  refreshCards(); // Replace skeleton cards as soon as the script loads
  setInterval(refreshCards, 10000);
} else {
  const _c = document.getElementById("game-cards-container");
  if (_c) { buildCarouselDots(); maybeShowSwipeHint(_c); }
}
