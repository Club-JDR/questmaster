document.addEventListener('DOMContentLoaded', function () {
  const confirmModal = document.getElementById('confirmArchive');
  const archiveBtn = document.getElementById('archiveBtn');
  let countdown;

  confirmModal.addEventListener('show.bs.modal', function () {
    let seconds = 10;
    archiveBtn.disabled = true;
    archiveBtn.textContent = `Archiver (${seconds})`;

    countdown = setInterval(() => {
      seconds--;
      if (seconds > 0) {
        archiveBtn.textContent = `Archiver (${seconds})`;
      } else {
        clearInterval(countdown);
        archiveBtn.textContent = "Archiver";
        archiveBtn.disabled = false;
      }
    }, 1000);
  });

  // Optional: Reset button if modal is closed early
  confirmModal.addEventListener('hide.bs.modal', function () {
    clearInterval(countdown);
    archiveBtn.textContent = "Archiver";
    archiveBtn.disabled = false;
  });
});