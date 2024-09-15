flatpickr('.flatpickr-start', {
  "locale": "fr",
  time_24hr: true,
  enableTime: true,
  allowInput: true,
  defaultHour: 20,
  defaultMinute: 30,
});
flatpickr('.flatpickr-end', {
  "locale": "fr",
  time_24hr: true,
  enableTime: true,
  allowInput: true,
  defaultHour: 23,
});

function validateDateRange(start, end, button) {
  if (new Date(document.querySelector(end)._flatpickr.selectedDates) > new Date(document.querySelector(start)._flatpickr.selectedDates)) {
    document.getElementById(button).disabled = false;
  } else {
    document.getElementById(button).disabled = true;
  }
}
