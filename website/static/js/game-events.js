  document.addEventListener('DOMContentLoaded', function () {
    // Archive modal countdown
    const confirmModal = document.getElementById('confirmArchive');
    const archiveBtn = document.getElementById('archiveBtn');
    const validateSessions = document.getElementById('validateSessions');
    let archiveCountdown;
    let countdownFinished = false;

    if (confirmModal && archiveBtn) {
      confirmModal.addEventListener('show.bs.modal', function () {
        let seconds = 10;
        countdownFinished = false;
        archiveBtn.disabled = true;
        archiveBtn.textContent = `Archiver (${seconds})`;

        archiveCountdown = setInterval(() => {
          seconds--;
          if (seconds > 0) {
            archiveBtn.textContent = `Archiver (${seconds})`;
          } else {
            clearInterval(archiveCountdown);
            countdownFinished = true;
            updateArchiveButtonState();
          }
        }, 1000);
      });

      confirmModal.addEventListener('hide.bs.modal', function () {
        clearInterval(archiveCountdown);
        countdownFinished = false;
        archiveBtn.textContent = "Archiver";
        archiveBtn.disabled = false;
      });

      // Vérifie si le switch "validateSessions" est activé avant d’autoriser l’archivage
      if (validateSessions) {
        validateSessions.addEventListener('change', updateArchiveButtonState);
      }

      function updateArchiveButtonState() {
        if (countdownFinished && validateSessions?.checked) {
          archiveBtn.disabled = false;
          archiveBtn.textContent = "Archiver";
        } else {
          archiveBtn.disabled = true;
          if (!countdownFinished) {
            archiveBtn.textContent = "Archiver (attendez la fin du compte à rebours)";
          } else {
            archiveBtn.textContent = "Archiver (sessions non validées)";
          }
        }
      }
    }


    // Signup button countdown logic
    const signupBtn = document.getElementById("signup-btn");
    const signupTimer = document.getElementById("signup-timer");

    if (signupBtn && signupTimer && !signupBtn.disabled) {
      let seconds = 10;
      signupBtn.disabled = true;
      signupTimer.textContent = `(${seconds})`;

      const signupCountdown = setInterval(() => {
        seconds -= 1;
        signupTimer.textContent = `(${seconds})`;

        if (seconds <= 0) {
          clearInterval(signupCountdown);
          signupBtn.disabled = false;
          signupTimer.textContent = '';
        }
      }, 1000);
    }
  });
