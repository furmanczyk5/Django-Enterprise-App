var newtheme = newtheme || {};

//namespace just in case
(function( o ){

  o.readMoreExpandable = function () {

    $readMoreExpandable = $('.read-more-expandable');

    if ($readMoreExpandable.length) init();

    function init () {


      $readMoreExpandable = $('.read-more-expandable');



      var hasChildren = $readMoreExpandable.children('p').length;

      if (hasChildren) {

        var firstChild = $readMoreExpandable.children('p').first();

        firstChild.siblings().hide();

        $readMoreExpandable.append('<div class="read-more-expandable-wrap"><a href="#" class="read-more-expandable-toggle">Show More</a></div>'); //put this in the dom first then move it

        $readMoreExpandable.find('.read-more-expandable-toggle').click(function (e) {
          e.preventDefault();

          $this = $(this);
          if ($this.hasClass('active')) {
            $this.removeClass('active').text('Read More');
            firstChild.siblings('p').hide();
          } else {
            $this.addClass('active').text('Read Less');
            firstChild.siblings('p').show();
          }


        });




      } else {
        return;
      }





    }


  }

})(newtheme);

$(function() {
  newtheme.readMoreExpandable();
});