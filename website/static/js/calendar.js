document.addEventListener("DOMContentLoaded", function () {
  const isMobile = window.innerWidth < 768;      // tweak your breakpoint here
  const calendarEl = document.getElementById("month-games-calendar");

  const calendar = new FullCalendar.Calendar(calendarEl, {
    themeSystem: 'bootstrap5',
    initialView: isMobile ? 'listMonth' : 'dayGridMonth',
    headerToolbar: isMobile
      ? { left: 'prev,next', center: 'title', right: 'listMonth' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listMonth' },
    buttonText: {
      today: 'Aujourd\'hui',
      month: 'Mois',
      week: 'Semaine',
      day: 'Jour',
      list: 'Liste'
    },
    locale: 'fr',
    timeZone: 'local',
    contentHeight: 'auto',
    events: function (fetchInfo, successCallback, failureCallback) {
      fetch(`/api/calendar?start=${fetchInfo.startStr}&end=${fetchInfo.endStr}`)
        .then(r => r.ok ? r.json() : Promise.reject("Network error"))
        .then(data => successCallback(data))
        .catch(err => failureCallback(err));
    },
    eventClick: function (info) {
      if (info.event.url) {
        window.open(info.event.url, "_blank");
        info.jsEvent.preventDefault();
      }
    },
  });

  calendar.render();

  // Re-render on orientation change or resize
  window.addEventListener('resize', () => {
    const newIsMobile = window.innerWidth < 768;
    if (newIsMobile !== isMobile) {
      calendar.changeView(newIsMobile ? 'listMonth' : 'dayGridMonth');
      calendar.setOption('headerToolbar', newIsMobile
        ? { left: 'prev,next', center: 'title', right: 'listMonth' }
        : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listMonth' });
    }
  });
});