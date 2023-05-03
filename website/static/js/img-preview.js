$('#imgSelect').click(function() {
    $('#imgPreview').attr('src', $("#imgLink").val());
    $('#imgPreview').attr('style', '');
    $('#imgPreviewContainer').hide();
});