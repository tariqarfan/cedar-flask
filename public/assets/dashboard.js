const dateElement = document.querySelector('#current-date');
const timeElement = document.querySelector('#current-time');
const dateFormat = new Intl.DateTimeFormat(undefined, {
  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
});
const timeFormat = new Intl.DateTimeFormat(undefined, {
  hour: '2-digit', minute: '2-digit', second: '2-digit'
});
document.querySelector('#current-timezone').textContent =
  `Local time · ${Intl.DateTimeFormat().resolvedOptions().timeZone}`;
function updateClock() {
  const now = new Date();
  dateElement.textContent = dateFormat.format(now);
  timeElement.textContent = timeFormat.format(now);
  timeElement.dateTime = now.toISOString();
  document.querySelector('#dashboard-year').textContent = now.getFullYear();
}
updateClock();
setInterval(updateClock, 1000);
