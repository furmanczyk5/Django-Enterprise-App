/* ////////////////////////////////
// Accordion
//////////////////////////////// */

var newtheme = newtheme || {};

(function( o ){

  o.initializeAccordions = function () {

    var $accordions = jQuery('.accordion');

    $accordions.each(function(){
      var $thisAccordion = jQuery(this);

      var $thisHandle = $thisAccordion.children('.accordion-handle');
      var $thisContent = $thisAccordion.children('.accordion-content');

      $thisHandle.on('click', function () {
        $thisAccordion.toggleClass('open');
      });

    });
  }
})(newtheme);

$(function() {
  newtheme.initializeAccordions();
});