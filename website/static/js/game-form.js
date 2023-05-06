// Datetime picker config
flatpickr.localize(flatpickr.l10ns.fr);
flatpickr('#calendar', {
    "locale": "fr",
    time_24hr: true,
    enableTime: true,
    allowInput: true,
    defaultHour: 20,
});

// Update image when URL is set
$('#imgSelect').click(function() {
    $('#imgPreview').attr('src', $("#imgLink").val());
    $('#imgPreview').attr('style', '');
});

// Read restriction_tags to create "tags" in the text field
var input = document.querySelector('#restriction_tags');
new Tagify(input, {
    delimiters: ",",
    transformTag: transformTag,
});

function getRandomColor() {
    function rand(min, max) {
        return min + Math.random() * (max - min);
    }

    var h = rand(1, 360) | 0,
        s = rand(40, 70) | 0,
        l = rand(65, 72) | 0;

    return 'hsl(' + h + ',' + s + '%,' + l + '%)';
}

function transformTag(tagData) {
    tagData.color = getRandomColor();
    tagData.style = "--tag-bg:" + tagData.color;

    if (tagData.value.toLowerCase() == 'shit')
        tagData.value = 's✲✲t'
}

// Change form fields size from 75% to 100% on mobile
if ($(window).width() < 1024) {
    $('.w-75').addClass('w-100');
    $('.w-100').removeClass('w-75');
}

// Add Markdown Editor
var simplemde = new SimpleMDE({
    element: $("#md-edit")[0],
    toolbar: ["bold", "italic", "heading", "|", "quote", "unordered-list", "link"],
    status: false,
    forceSync: true,
    indentWithTabs: false,
    spellChecker: false,
});

// Needed for form validation
(() => {
    'use strict'
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    const forms = document.querySelectorAll('.needs-validation')
        // Loop over them and prevent submission
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }
            if (simplemde.value().trim() == '') {
                $('.cm-s-paper').addClass('form-control is-invalid');
                $('.cm-s-paper').removeClass('is-valid');
            } else {
                $('.cm-s-paper').addClass('is-valid');
                $('.cm-s-paper').removeClass('is-invalid');
            }
            form.classList.add('was-validated')
        }, false)
    })
})()

// form validation for simpleMDE
function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}
delay(1000).then(() =>
    $('.CodeMirror-scroll').on('DOMSubtreeModified', function() {
        if (simplemde.value().trim() == '') {
            $('.cm-s-paper').addClass('form-control is-invalid');
            $('.cm-s-paper').removeClass('is-valid');
        } else {
            $('.cm-s-paper').addClass('is-valid');
            $('.cm-s-paper').removeClass('is-invalid');
        }
    })
);