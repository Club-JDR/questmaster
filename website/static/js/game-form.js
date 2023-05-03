flatpickr.localize(flatpickr.l10ns.fr);
flatpickr('#calendar', {
    "locale": "fr",
    time_24hr: true,
    enableTime: true,
    allowInput: true,
    defaultHour: 20,
});

$('#imgSelect').click(function() {
    $('#imgPreview').attr('src', $("#imgLink").val());
    $('#imgPreview').attr('style', '');
});

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

var simplemde = new SimpleMDE({ element: document.getElementById("md-edit"), spellChecker: false, toolbar: ["bold", "italic", "heading", "|", "quote", "unordered-list", "link", "preview"], });