  document.addEventListener('DOMContentLoaded', function () {
    // Archive modal countdown
    const confirmModal = document.getElementById('confirmArchive');
    const archiveBtn = document.getElementById('archiveBtn');
    let archiveCountdown;

    if (confirmModal && archiveBtn) {
      confirmModal.addEventListener('show.bs.modal', function () {
        let seconds = 10;
        archiveBtn.disabled = true;
        archiveBtn.textContent = `Archiver (${seconds})`;

        archiveCountdown = setInterval(() => {
          seconds--;
          if (seconds > 0) {
            archiveBtn.textContent = `Archiver (${seconds})`;
          } else {
            clearInterval(archiveCountdown);
            archiveBtn.textContent = "Archiver";
            archiveBtn.disabled = false;
          }
        }, 1000);
      });

      confirmModal.addEventListener('hide.bs.modal', function () {
        clearInterval(archiveCountdown);
        archiveBtn.textContent = "Archiver";
        archiveBtn.disabled = false;
      });
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
