// Pre-fill date to today at 20:30 for new games
(function () {
  var d = document.getElementById("game_date");
  if (d && !d.value) {
    var now = new Date();
    var pad = function (n) {
      return String(n).padStart(2, "0");
    };
    d.value =
      now.getFullYear() +
      "-" +
      pad(now.getMonth() + 1) +
      "-" +
      pad(now.getDate()) +
      "T20:30";
  }
})();

// Auto-resize textareas to always show full content without scrolling
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = el.scrollHeight + "px";
  el.style.overflowY = "hidden";
}
document.querySelectorAll("textarea.auto-resize").forEach(function (ta) {
  autoResize(ta);
  ta.addEventListener("input", function () {
    autoResize(this);
  });
});

// Classification range sliders → Absent / Mineur / Majeur label
var classLabels = ["Absent", "Mineur", "Majeur"];
document.querySelectorAll("input[type=range].range").forEach(function (range) {
  var lbl = document.querySelector(
    '.classification-label[data-for="' + range.id + '"]'
  );
  if (lbl) {
    range.addEventListener("input", function () {
      lbl.textContent = classLabels[this.value];
    });
  }
});

// Warn before publishing a draft whose start date is in the past: its first
// session would be created in the past. The server enforces this too (a
// PastDateError), so this modal is a friendlier front line, not the guardrail.
(function () {
  var form = document.querySelector("form");
  var dateInput = document.getElementById("game_date");
  var confirmField = document.getElementById("confirmPastDate");
  var modal = document.getElementById("pastDateModal");
  if (!form || !dateInput || !confirmField || !modal) return;

  var pendingSubmitter = null;

  form.addEventListener("submit", function (e) {
    var submitter = e.submitter;
    // Only publishing actions create the first session; drafts are exempt.
    if (!submitter || (submitter.value !== "open" && submitter.value !== "open-silent")) {
      return;
    }
    if (confirmField.value === "1") return; // already confirmed
    if (!dateInput.value) return;
    if (new Date(dateInput.value) >= new Date()) return; // not in the past

    e.preventDefault();
    pendingSubmitter = submitter;
    modal.showModal();
  });

  var confirmBtn = document.getElementById("confirmPastDateBtn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", function () {
      confirmField.value = "1";
      modal.close();
      form.requestSubmit(pendingSubmitter || undefined);
    });
  }

  var changeBtn = document.getElementById("changeDateBtn");
  if (changeBtn) {
    changeBtn.addEventListener("click", function () {
      modal.close();
      dateInput.focus();
      if (typeof dateInput.showPicker === "function") {
        try {
          dateInput.showPicker();
        } catch (err) {
          /* showPicker may throw if not user-activated; focus is enough */
        }
      }
    });
  }
})();

// Image URL preview with timeout-based validation
(function () {
  var input = document.getElementById("imgUrlInput");
  var preview = document.getElementById("imgPreview");
  var error = document.getElementById("imgError");
  var testImg = null;
  var timeout = null;
  var PLACEHOLDER = "/static/img/placeholder.jpeg";

  // Users often paste an imgur *page* URL (imgur.com/abc123) instead of the
  // direct image URL — imgur's "grab a link" only offers the page link. imgur's
  // CDN serves the image under any extension, so rewrite single-image page URLs
  // to a direct .webp (transparency-safe, small). Albums/galleries (which have a
  // second path segment), already-direct i.imgur.com links and non-imgur URLs
  // are left untouched.
  function normalizeImgur(url) {
    var m = /^https?:\/\/(?:www\.|m\.)?imgur\.com\/([A-Za-z0-9]+)\/?$/.exec(url);
    if (!m || ["a", "gallery", "t"].indexOf(m[1]) !== -1) return url;
    return "https://i.imgur.com/" + m[1] + ".webp";
  }

  function loadImage(url) {
    if (testImg) {
      testImg.onload = testImg.onerror = null;
      testImg = null;
    }
    clearTimeout(timeout);
    error.classList.add("hidden");
    if (!url) {
      preview.src = PLACEHOLDER;
      return;
    }
    testImg = new Image();
    timeout = setTimeout(function () {
      preview.src = PLACEHOLDER;
      error.classList.remove("hidden");
      testImg = null;
    }, 4000);
    testImg.onload = function () {
      clearTimeout(timeout);
      preview.src = url;
      error.classList.add("hidden");
      testImg = null;
    };
    testImg.onerror = function () {
      clearTimeout(timeout);
      preview.src = PLACEHOLDER;
      error.classList.remove("hidden");
      testImg = null;
    };
    testImg.src = url;
  }

  if (input) {
    input.addEventListener("input", function () {
      loadImage(this.value.trim());
    });
    // Rewrite an imgur page URL to its direct image URL when leaving the field.
    input.addEventListener("blur", function () {
      var trimmed = this.value.trim();
      var normalized = normalizeImgur(trimmed);
      if (normalized !== trimmed) {
        this.value = normalized;
        loadImage(normalized);
      }
    });
    if (input.value) loadImage(input.value.trim());
  }
})();
