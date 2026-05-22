document.addEventListener("DOMContentLoaded", function () {
  var isMobile = window.innerWidth < 768;
  var calendarEl = document.getElementById("month-games-calendar");

  var calendar = new FullCalendar.Calendar(calendarEl, {
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
      QuestMasterAPI.get('/calendar/events/', {
        start: fetchInfo.startStr,
        end: fetchInfo.endStr,
      })
        .then(function (data) {
          var events = data.map(function (item) {
            return {
              id: item.id,
              title: item.title,
              start: item.start,
              end: item.end,
              color: item.color,
              className: item.type === 'oneshot' ? 'event-oneshot' : 'event-campaign',
              url: '/annonces/' + item.game_slug + '/',
            };
          });
          successCallback(events);
        })
        .catch(function (err) {
          failureCallback(err);
        });
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
  window.addEventListener('resize', function () {
    var newIsMobile = window.innerWidth < 768;
    if (newIsMobile !== isMobile) {
      calendar.changeView(newIsMobile ? 'listMonth' : 'dayGridMonth');
      calendar.setOption('headerToolbar', newIsMobile
        ? { left: 'prev,next', center: 'title', right: 'listMonth' }
        : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listMonth' });
    }
  });
});
