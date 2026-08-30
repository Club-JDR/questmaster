import { Calendar } from 'fullcalendar';
import dayGridPlugin from 'fullcalendar/daygrid';
import listPlugin from 'fullcalendar/list';
import classicThemePlugin from 'fullcalendar/themes/classic';
import frLocale from 'fullcalendar/locales/fr';

import 'fullcalendar/skeleton.css';
import 'fullcalendar/themes/classic/theme.css';
import 'fullcalendar/themes/classic/palette.css';
import '../css/calendar-theme.css';

document.addEventListener('DOMContentLoaded', function () {
  let isMobile = window.innerWidth < 768;
  const calendarEl = document.getElementById('month-games-calendar');

  const calendar = new Calendar(calendarEl, {
    plugins: [dayGridPlugin, listPlugin, classicThemePlugin],
    initialView: isMobile ? 'listMonth' : 'dayGridMonth',
    headerToolbar: isMobile
      ? { left: 'prev,next', center: 'title', right: 'listMonth' }
      : { left: 'prev,next today', center: 'title', right: 'dayGridMonth,listMonth' },
    buttons: {
      today: { text: "Aujourd'hui" },
      dayGridMonth: { text: 'Mois' },
      listMonth: { text: 'Liste' },
    },
    locale: frLocale,
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
