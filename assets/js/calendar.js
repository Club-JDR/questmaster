import { Calendar } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import listPlugin from '@fullcalendar/list';

document.addEventListener('DOMContentLoaded', function () {
  let isMobile = window.innerWidth < 768;
  const calendarEl = document.getElementById('month-games-calendar');

  const calendar = new Calendar(calendarEl, {
    plugins: [dayGridPlugin, listPlugin],
    initialView: isMobile ? 'listMonth' : 'dayGridMonth',
    headerToolbar: isMobile
      ? { left: 'prev,next', center: 'title', right: 'listMonth' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listMonth' },
    buttonText: {
      today: "Aujourd'hui",
      month: 'Mois',
      week: 'Semaine',
      day: 'Jour',
      list: 'Liste',
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
          const events = data.map(function (item) {
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
        window.open(info.event.url, '_blank');
        info.jsEvent.preventDefault();
      }
    },
  });

  calendar.render();

  window.addEventListener('resize', function () {
    const newIsMobile = window.innerWidth < 768;
    if (newIsMobile !== isMobile) {
      isMobile = newIsMobile;
      calendar.changeView(newIsMobile ? 'listMonth' : 'dayGridMonth');
      calendar.setOption(
        'headerToolbar',
        newIsMobile
          ? { left: 'prev,next', center: 'title', right: 'listMonth' }
          : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listMonth' }
      );
    }
  });
});
