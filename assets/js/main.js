// @ts-ignore — no type declarations for this side-effect import
import "@phosphor-icons/web/regular";
// @ts-ignore
import "@phosphor-icons/web/bold";
// @ts-ignore
import "@phosphor-icons/web/fill";

const getSavedTheme = () =>
  localStorage.getItem("theme") ||
  (globalThis.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

document.documentElement.dataset.theme = getSavedTheme();

document.addEventListener("click", (e) => {
  document.querySelectorAll(".menu details[open]").forEach((details) => {
    if (!details.contains(/** @type {Node} */ (e.target))) {
      details.removeAttribute("open");
    }
  });
});

// 3D card tilt — follows mouse position, works for dynamically injected cards
document.addEventListener("mousemove", (e) => {
  const el = /** @type {Element|null} */ (e.target);
  const card = /** @type {HTMLElement|null} */ (el?.closest(".game-card"));
  if (!card) return;
  const rect = card.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const rx = ((rect.height / 2 - y) / (rect.height / 2)) * 10;
  const ry = ((x - rect.width / 2) / (rect.width / 2)) * 10;
  card.style.transition = "transform 0.08s ease, box-shadow 0.15s ease";
  card.style.transform = `rotateX(${rx}deg) rotateY(${ry}deg) scale(1.02)`;
  card.style.boxShadow = "0 20px 40px rgba(0,0,0,0.18)";
});

document.addEventListener("mouseout", (e) => {
  const el = /** @type {Element|null} */ (e.target);
  const card = /** @type {HTMLElement|null} */ (el?.closest(".game-card"));
  if (!card) return;
  if (card.contains(/** @type {Node} */ (e.relatedTarget))) return;
  card.style.transition = "transform 0.4s ease, box-shadow 0.4s ease";
  card.style.transform = "";
  card.style.boxShadow = "";
});

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input.theme-controller").forEach((el) => {
    const input = /** @type {HTMLInputElement} */ (el);
    input.checked = input.value === getSavedTheme();
    input.addEventListener("change", () => {
      const theme = input.value;
      document.documentElement.dataset.theme = theme;
      localStorage.setItem("theme", theme);
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
    });
  });
});
