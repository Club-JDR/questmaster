function refreshCards() {
  const params = new URLSearchParams(window.location.search);
  fetch(`/annonces/cards/?${params.toString()}`)
    .then(response => response.text())
    .then(html => {
      document.getElementById("game-cards-container").innerHTML = html;
    });
}

// Poll every 10 seconds
setInterval(refreshCards, 10000);