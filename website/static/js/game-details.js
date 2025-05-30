function refreshGameDetails() {
    const container = document.getElementById("game-details-container");
    const gameId = container?.dataset?.gameId;
    if (!gameId) return;

    fetch(`/annonces/${gameId}/details`)
      .then(response => response.text())
      .then(html => {
        const temp = document.createElement("div");
        temp.innerHTML = html.trim();
        const newDetails = temp.querySelector("#game-details-container");
        if (newDetails) {
          container.replaceWith(newDetails);
        }
      })
      .catch(error => {
        console.error("Failed to refresh game details:", error);
      });
}

// Poll every 10 seconds
setInterval(refreshGameDetails, 10000);