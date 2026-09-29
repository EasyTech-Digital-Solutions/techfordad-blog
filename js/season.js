// Seasonal theme switch. Sets <html data-season="halloween|christmas"> from the visitor's
// local date; css/style.css does the rest. Outside the windows below nothing is set, so the
// default look is used. Kept tiny and loaded in <head> so the theme is in place before first paint.
//   Halloween: Sep 29 - Oct 31      Christmas: Nov 1 - Dec 31
// Preview: add ?season=halloween, ?season=christmas or ?season=none to any page URL.
(function () {
  var root = document.documentElement;
  var season = '';
  try {
    var override = new URLSearchParams(location.search).get('season');
    if (override) {
      season = override === 'none' ? '' : override;
    } else {
      var now = new Date();
      var month = now.getMonth() + 1;
      var day = now.getDate();
      if ((month === 9 && day >= 29) || month === 10) season = 'halloween';
      else if (month === 11 || month === 12) season = 'christmas';
    }
  } catch (e) { /* keep the default look */ }
  if (season === 'halloween' || season === 'christmas') root.setAttribute('data-season', season);
})();
