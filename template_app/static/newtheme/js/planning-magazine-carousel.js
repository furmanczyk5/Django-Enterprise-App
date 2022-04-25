jQuery(function($) {

  var planningMagSlider = $('.planning .addtl_articles .slider');

  //if window is otherwise resized, reinit slider if it's disabled
  $(window).on('resize orientationchange', function () {
    planningMagSlider.not('.slick-initialized').slick('reinit');
  });

  planningMagSlider.each(function(){

    $(this).before('<div class="dots-nav">');

    $(this).slick({

      infinite: false,
      dots: false,
      appendDots: $(this).prev(), //targets newly created .dots-nav div
      adaptiveHeight: true,
      arrows: false,
      responsive: [
        {
          breakpoint: 9999,
          settings: "unslick"
        },
        {
          breakpoint: 1300,
          settings: {
            dots: true,
            slidesToShow: 4,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 992,
          settings: {
            dots: true,
            slidesToShow: 3.5,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 640,
          settings: {
            dots: true,
            slidesToShow: 2.5,
            slidesToScroll: 1
          }
        },
        {
          breakpoint: 420,
          settings: {
            dots: true,
            slidesToShow: 1.5,
            slidesToScroll: 1
          }
        }
      ]
    }); //end slick method

  }); //end each

});
