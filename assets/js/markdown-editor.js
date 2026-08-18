// Markdown editor for game description/complement textareas: a formatting
// toolbar plus a preview toggle, backed by EasyMDE. The underlying <textarea>
// remains the actual form field (EasyMDE mirrors its value into it), so
// submission is unaffected — only Markdown source is ever posted/stored.
import EasyMDE from "easymde";
// @ts-ignore — no type declarations for this side-effect import
import "easymde/dist/easymde.min.css";

// Adds the project's `prose` typography classes (also used to render the
// saved Markdown on the game details page) to EasyMDE's preview pane, so the
// live preview matches the final rendering instead of looking unstyled.
function togglePreviewWithProse(editor) {
  EasyMDE.togglePreview(editor);
  const preview = editor.codemirror.getWrapperElement().querySelector(".editor-preview-full");
  if (preview) preview.classList.add("prose", "prose-sm", "max-w-none", "p-4");
}

// Reuse the project's Phosphor icon set for toolbar buttons instead of
// pulling in Font Awesome (EasyMDE's default), keeping a single icon system.
// `noDisable: true` on preview/guide matches EasyMDE's own built-in toolbar
// item definitions — without it, the toolbar gets stuck disabled once
// preview mode is entered, since these are exactly the buttons meant to
// stay clickable while editing is disabled (to be able to toggle back out).
const TOOLBAR = [
  { name: "bold", action: EasyMDE.toggleBold, className: "ph ph-text-b", title: "Gras" },
  { name: "italic", action: EasyMDE.toggleItalic, className: "ph ph-text-italic", title: "Italique" },
  { name: "heading", action: EasyMDE.toggleHeadingSmaller, className: "ph ph-text-h", title: "Titre" },
  "|",
  { name: "quote", action: EasyMDE.toggleBlockquote, className: "ph ph-quotes", title: "Citation" },
  { name: "unordered-list", action: EasyMDE.toggleUnorderedList, className: "ph ph-list-bullets", title: "Liste à puces" },
  { name: "ordered-list", action: EasyMDE.toggleOrderedList, className: "ph ph-list-numbers", title: "Liste numérotée" },
  "|",
  { name: "link", action: EasyMDE.drawLink, className: "ph ph-link", title: "Lien" },
  "|",
  { name: "preview", action: togglePreviewWithProse, className: "ph ph-eye", title: "Aperçu", noDisable: true },
  { name: "guide", action: "https://www.markdownguide.org/basic-syntax/", className: "ph ph-question", title: "Aide Markdown", noDisable: true },
];

// CodeMirror (which EasyMDE wraps) hides the original <textarea> via
// `display: none` once it takes over. A `required` textarea that's hidden
// can't be focused, so on submit the browser's native constraint validation
// blocks the form *silently* — no error bubble, no visible feedback, the
// click just appears to do nothing (worst on forms like game creation where
// the description starts empty, e.g. branching a campaign into a one-shot).
// Drop `required` from the hidden element and enforce it ourselves against
// the visible editor instead, with a clear on-screen error when it fails.
function guardRequiredEditor(el, editor) {
  if (!el.required) return;
  el.required = false;

  var wrapper = editor.codemirror.getWrapperElement();
  var form = el.closest("form");
  if (!form) return;

  // A border alone is easy to miss (and CodeMirror's own styles can mask
  // it) — pair it with an explicit, always-legible error message, matching
  // the app's other inline field errors (e.g. #imgError).
  var errorMsg = document.createElement("p");
  errorMsg.className = "hidden text-xs text-error-accent flex items-center gap-1 mt-1";
  errorMsg.setAttribute("role", "alert");
  errorMsg.innerHTML = '<i class="ph ph-warning" aria-hidden="true"></i> Ce champ est requis.';
  wrapper.insertAdjacentElement("afterend", errorMsg);

  // EasyMDE/CodeMirror ship their own `.CodeMirror { border: ... }` rule at
  // the same specificity as a Tailwind utility class, loaded after
  // main.css — so a `border-error` *class* on the wrapper silently loses
  // the cascade. Setting the border directly as an inline style reliably
  // wins over any non-!important stylesheet rule regardless of load order.
  function clearError() {
    wrapper.style.removeProperty("border-color");
    wrapper.style.removeProperty("border-width");
    errorMsg.classList.add("hidden");
  }

  form.addEventListener("submit", function (e) {
    if (editor.value().trim()) {
      clearError();
      return;
    }
    e.preventDefault();
    wrapper.style.borderColor = "var(--color-error)";
    wrapper.style.borderWidth = "2px";
    errorMsg.classList.remove("hidden");
    wrapper.scrollIntoView({ behavior: "smooth", block: "center" });
    editor.codemirror.focus();
  });

  editor.codemirror.on("change", function () {
    if (editor.value().trim()) clearError();
  });
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("textarea[data-markdown-editor]").forEach(function (el) {
    var editor = new EasyMDE({
      element: el,
      spellChecker: false,
      status: false,
      autoDownloadFontAwesome: false,
      toolbar: TOOLBAR,
      minHeight: el.dataset.minHeight || "150px",
      placeholder: el.getAttribute("placeholder") || "",
    });
    guardRequiredEditor(el, editor);
  });
});
