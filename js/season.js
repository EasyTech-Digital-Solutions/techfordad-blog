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

  // Gift Guides feature on the homepage: bigger and higher in gift season.
  //   Peak: Sep 1 - Dec 31 (Grandparents Day through the holidays), May 1-14 (Mother's Day), Jun 1-21 (Father's Day).
  // Preview: ?gifts=peak or ?gifts=off
  var gifts = 'off';
  try {
    var g = new URLSearchParams(location.search).get('gifts');
    if (g === 'peak' || g === 'off') {
      gifts = g;
    } else {
      var d2 = new Date(), m2 = d2.getMonth() + 1, day2 = d2.getDate();
      if (m2 >= 9 || (m2 === 5 && day2 <= 14) || (m2 === 6 && day2 <= 21)) gifts = 'peak';
    }
  } catch (e) { /* keep default */ }
  root.setAttribute('data-gifts', gifts);

  // The gift announcement bar stays hidden for 14 days after a visitor dismisses it.
  // Set here, before first paint, so a dismissed bar never flashes back in.
  // Preview the bar again with ?giftbar=show.
  try {
    var closedAt = parseInt(localStorage.getItem('giftBarClosed') || '0', 10);
    var forceShow = new URLSearchParams(location.search).get('giftbar') === 'show';
    if (forceShow) localStorage.removeItem('giftBarClosed');
    else if (closedAt && Date.now() - closedAt < 14 * 24 * 60 * 60 * 1000) root.setAttribute('data-gift-bar', 'closed');
  } catch (e) { /* storage blocked: the bar simply stays visible */ }
})();
