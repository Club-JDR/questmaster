/** @type {HTMLElement | null} */
let _staleToast = null;

function refreshCards() {
  const params = new URLSearchParams(window.location.search);
  const container = globalThis.document.getElementById("game-cards-container");
  if (!container) return;

  fetch(`/annonces/cards/?${params.toString()}`)
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.text();
    })
    .then(function (html) {
      container.innerHTML = html;
      if (_staleToast) { _staleToast.remove(); _staleToast = null; }
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

// Poll every 10 seconds
setInterval(refreshCards, 10000);