/* //////////////////////////////////
// Custom conference countdown
////////////////////////////////// */
var newtheme = newtheme || {};

(function (o) {
  o.initializeConferenceCountdown = function (targetDate) {
    // grab all the nodes
    var $daysNode = $('#conference-countdown-days').children('.count');
    var $hoursNode = $('#conference-countdown-hours').children('.count');
    var $minutesNode = $('#conference-countdown-minutes').children('.count');
    var $secondsNode = $('#conference-countdown-seconds').children('.count');


// Update the count down every 1 second
    var x = setInterval(function () {

      // Get todays date and time
      var now = new Date().getTime();

      // Find the distance between now an the count down date
      var distance = targetDate - now;

      // Time calculations for days, hours, minutes and seconds
      var days = Math.floor(distance / (1000 * 60 * 60 * 24));
      var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      var seconds = Math.floor((distance % (1000 * 60)) / 1000);

      // Display the result
      $daysNode.text(days);
      $hoursNode.text(hours);
      $minutesNode.text(minutes);
      $secondsNode.text(seconds);

      // If the count down is finished, write some text
      if (distance < 0) {
        clearInterval(x);
        $daysNode.text(0);
        $hoursNode.text(0);
        $minutesNode.text(0);
        $secondsNode.text(0);
      }
    }, 1000);

  };
})(newtheme);

$(function () {

  var earlyBirdDate = new Date("March 5, 2020 00:01:00").getTime();
  var conferenceDate = new Date("April 25, 2020 08:00:00").getTime();
  var $headingText = $('.conference-countdown-heading');

  var now = new Date().getTime();
  if (now < earlyBirdDate) {
    // display: none by default (setting the hidden attribute on the <div> didn't work)
    $('#conference-countdown').css('display', 'block');
    $headingText.text('Early bird registration ends March 4. Get the best price on NPC20!');
    newtheme.initializeConferenceCountdown(earlyBirdDate);
  } else if (now < conferenceDate) {
    $('#conference-countdown').css('display', 'block');
    $headingText.text('Conference countdown! Houston, here we come!');
    newtheme.initializeConferenceCountdown(conferenceDate);
  }
});
