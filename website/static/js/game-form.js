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
    delimiters: ","
});


// Change form fields size from 75% to 100% on mobile
if ($(window).width() < 1024) {
    $('.w-75').addClass('w-100');
    $('.w-100').removeClass('w-75');
}

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
            form.classList.add('was-validated')
        }, false)
    })
})()

  const labels = ['Absent', 'Mineur', 'Majeur'];

  document.querySelectorAll('.form-range').forEach(slider => {
    slider.addEventListener('input', function () {
      const labelSpan = document.querySelector(`.form-range-label[data-for="${this.id}"]`);
      labelSpan.textContent = labels[this.value];
    });
  });