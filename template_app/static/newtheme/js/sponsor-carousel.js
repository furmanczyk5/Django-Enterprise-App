/* ////////////////////////
// Sponsor carousel (conference homepage)
//////////////////////// */
var newtheme = newtheme || {};

(function( o ){

  o.initializeSponsorCarousels = function () {

    jQuery('.sponsor-carousel').slick({
      infinite: true,
      slidesToShow: 4,
      slidesToScroll: 1,
      prevArrow: '<button type="button" class="slick-prev icon-arrow-icon"></button>',
      nextArrow: '<button type="button" class="slick-next icon-arrow-icon"></button>',
      dots: false,
      //Note that responsive is desktop-first for slick carousel
      responsive: [
        {
          breakpoint: 1300,
          settings: {
            slidesToShow: 3,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 700,
          settings: {
            slidesToShow: 2,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 480,
          settings: {
            slidesToShow: 1,
            slidesToScroll: 1
          }
        }
      ]
    });

  };

})(newtheme);

$(function() {
  newtheme.initializeSponsorCarousels();
});