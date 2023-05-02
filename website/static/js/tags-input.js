var input = document.querySelector('#restrictionTags');
new Tagify(input, {
    delimiters: ",",
    transformTag: transformTag,
});
// generate a random color (in HSL format, which I like to use)
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