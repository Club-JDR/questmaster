  document.addEventListener("DOMContentLoaded", function () {
    const calendarEl = document.getElementById("month-games-calendar");
    const calendar = new FullCalendar.Calendar(calendarEl, {
      themeSystem: 'bootstrap5',
      initialView: 'dayGridMonth',
      locale: 'fr',
      timeZone: 'local',
      events: function (fetchInfo, successCallback, failureCallback) {
        const start = fetchInfo.startStr;
        const end = fetchInfo.endStr;

        fetch(`/api/calendar?start=${start}&end=${end}`)
          .then(response => {
            if (!response.ok) throw new Error("Network error");
            return response.json();
          })
          .then(data => successCallback(data))
          .catch(error => failureCallback(error));
      },
      eventClick: function (info) {
        if (info.event.url) {
          window.open(info.event.url, "_blank");
          info.jsEvent.preventDefault();
        }
      },
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,listMonth'
      },
    });

    calendar.render();
  });