/**
 * Add-player typeahead: search users by Discord username (or display name) and
 * resolve the selection to a hidden discord_id, so the existing add-player form
 * backend is unchanged. A raw Discord ID typed by hand is still accepted as a
 * fallback.
 *
 * Markup contract (see game_details.j2, trophies.j2):
 *   [data-user-typeahead]
 *     input[role=combobox]            visible search box
 *     ul[role=listbox]                suggestions dropdown
 *     input[type=hidden]              carries the resolved user id (any name —
 *                                     "discord_id" for add-player, "user_id"
 *                                     for the badges lookup)
 *     button[type=submit]             submits the enclosing form
 *     [data-typeahead-error]          inline error message (role=alert)
 *
 * Accessibility: WAI-ARIA combobox pattern — aria-expanded, aria-controls,
 * aria-activedescendant, full keyboard support (↑/↓/Enter/Esc) and a visible
 * focus ring inherited from DaisyUI inputs/menu items.
 */
(function () {
  const SEARCH_URL = "/api/v1/users/search/";
  const DEBOUNCE_MS = 250;
  const ID_RE = /^\d{17,21}$/;

  function initTypeahead(root) {
    const input = root.querySelector('input[role="combobox"]');
    const listbox = root.querySelector('[role="listbox"]');
    const hidden = root.querySelector('input[type="hidden"]');
    const addBtn = root.querySelector('button[type="submit"]');
    const error = root.querySelector("[data-typeahead-error]");
    // "Navigate on select" mode: when present, picking a suggestion goes
    // straight to this URL (with {id} substituted) instead of populating a
    // hidden field and submitting a form (used by the admin user list).
    const selectUrl = root.getAttribute("data-select-url");
    if (!input || !listbox || (!hidden && !selectUrl)) return;
    const optPrefix = (listbox.id || "user-search") + "-opt-";

    let results = [];
    let active = -1;
    let timer = null;
    let seq = 0;

    function clearError() {
      if (error) {
        error.textContent = "";
        error.classList.add("hidden");
      }
    }

    function showError(msg) {
      if (error) {
        error.textContent = msg;
        error.classList.remove("hidden");
      }
    }

    function close() {
      listbox.classList.add("hidden");
      listbox.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      results = [];
      active = -1;
    }

    function render() {
      listbox.innerHTML = "";
      results.forEach(function (user, i) {
        const li = document.createElement("li");
        li.id = optPrefix + i;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", i === active ? "true" : "false");

        const a = document.createElement("a");
        a.className = "flex items-center gap-2" + (i === active ? " menu-active" : "");
        const img = document.createElement("img");
        img.src = user.avatar;
        img.alt = "";
        img.className = "w-6 h-6 rounded-full";
        const span = document.createElement("span");
        span.className = "truncate";
        // textContent only — never innerHTML — to avoid injection.
        span.textContent = user.username
          ? user.name + " (" + user.username + ")"
          : user.name;
        a.appendChild(img);
        a.appendChild(span);

        a.addEventListener("mousedown", function (e) {
          e.preventDefault(); // keep focus on the input
          select(i);
        });
        li.appendChild(a);
        listbox.appendChild(li);
      });
      listbox.classList.toggle("hidden", results.length === 0);
      input.setAttribute("aria-expanded", results.length ? "true" : "false");
    }

    function setActive(i) {
      active = i;
      const opts = listbox.querySelectorAll('[role="option"]');
      opts.forEach(function (li, idx) {
        const a = li.querySelector("a");
        li.setAttribute("aria-selected", idx === i ? "true" : "false");
        if (a) a.classList.toggle("menu-active", idx === i);
      });
      if (i >= 0 && opts[i]) {
        input.setAttribute("aria-activedescendant", opts[i].id);
        opts[i].scrollIntoView({ block: "nearest" });
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    }

    function select(i) {
      const user = results[i];
      if (!user) return;
      if (selectUrl) {
        window.location.href = selectUrl.replace("{id}", encodeURIComponent(user.id));
        return;
      }
      hidden.value = user.id;
      input.value = user.username ? user.name + " (" + user.username + ")" : user.name;
      clearError();
      close();
    }

    function fetchUsers(term) {
      const mine = ++seq;
      fetch(SEARCH_URL + "?q=" + encodeURIComponent(term), {
        headers: { Accept: "application/json" },
      })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (data) {
          if (mine !== seq) return; // a newer request superseded this one
          results = Array.isArray(data) ? data : [];
          active = -1;
          render();
        })
        .catch(function () {
          if (mine !== seq) return;
          close();
        });
    }

    input.addEventListener("input", function () {
      // A new search invalidates any previously resolved selection.
      if (hidden) hidden.value = "";
      clearError();
      const term = input.value.trim();
      window.clearTimeout(timer);
      if (term.length < 2) {
        close();
        return;
      }
      timer = window.setTimeout(function () {
        fetchUsers(term);
      }, DEBOUNCE_MS);
    });

    input.addEventListener("keydown", function (e) {
      if (listbox.classList.contains("hidden")) {
        if (e.key === "ArrowDown" && input.value.trim().length >= 2) {
          fetchUsers(input.value.trim());
          e.preventDefault();
        }
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive((active + 1) % results.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive((active - 1 + results.length) % results.length);
      } else if (e.key === "Enter") {
        if (active >= 0) {
          e.preventDefault();
          select(active);
        }
      } else if (e.key === "Escape") {
        close();
      }
    });

    input.addEventListener("blur", function () {
      // Delay so a mousedown selection on an option runs first.
      window.setTimeout(close, 150);
    });

    // On submit via the "add" button, ensure the hidden id is populated. If the
    // user typed a raw Discord ID without picking a suggestion, accept it
    // directly; otherwise require an explicit pick to avoid the wrong person.
    // Skipped in navigate-on-select mode (no hidden field / form submit).
    if (addBtn && hidden) {
      addBtn.addEventListener("click", function (e) {
        if (hidden.value) return; // a suggestion was already selected
        const term = input.value.trim().replace(/^@/, "");
        if (ID_RE.test(term)) {
          hidden.value = term;
          return;
        }
        e.preventDefault();
        showError(
          "Choisissez une personne dans la liste ou saisissez un ID Discord."
        );
      });
    }
  }

  document.querySelectorAll("[data-user-typeahead]").forEach(initTypeahead);
})();
