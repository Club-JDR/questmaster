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

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("textarea[data-markdown-editor]").forEach(function (el) {
    new EasyMDE({
      element: el,
      spellChecker: false,
      status: false,
      autoDownloadFontAwesome: false,
      toolbar: TOOLBAR,
      minHeight: el.dataset.minHeight || "150px",
      placeholder: el.getAttribute("placeholder") || "",
    });
  });
});
