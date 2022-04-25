/* ////////////////////////////////
// Ads carousels
///////////////////////////////// */

var newtheme = newtheme || {};

(function( o ){

  o.initializeAdsCarousels = function () {
    jQuery('.layout-banner-ad-small-3up').each(function () {
      var $this = jQuery(this);

      var $banners = $this.find('.banner-ad');

      var firstIndex = 0;
      var lastIndex = $banners.length - 1;

      var currentIndex = -1;

      var rotateInterval = 8000;

      function rotateFn() {
        currentIndex++;

        if(currentIndex > lastIndex) {
          currentIndex = firstIndex;
        }

        //New current index
        $banners.eq(currentIndex).removeClass('rotate-hide').siblings().addClass('rotate-hide');
      }

      rotateFn();
      var clearableInterval = setInterval(rotateFn, rotateInterval);

    });

  }
})(newtheme);

$(function() {
  newtheme.initializeAdsCarousels();
});