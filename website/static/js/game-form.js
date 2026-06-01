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

// Image URL preview with timeout-based validation
(function () {
  var input = document.getElementById("imgUrlInput");
  var preview = document.getElementById("imgPreview");
  var error = document.getElementById("imgError");
  var testImg = null;
  var timeout = null;
  var PLACEHOLDER = "/static/img/placeholder.jpeg";

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
    if (input.value) loadImage(input.value.trim());
  }
})();
