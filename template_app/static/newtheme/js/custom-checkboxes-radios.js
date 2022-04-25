/* //////////////////////////////////
// Custom checkbox/radio styles
////////////////////////////////// */
var newtheme = newtheme || {};

(function( o ){
  o.initializeCustomCheckboxesAndRadios = function () {
  	// DOoWe Want to do this for every checkbox and radio?
  	// THIS BREAKS CHANGE EVENT FUNCTIONALITY, so added "not" to the query to prevent when we don't need this
    jQuery('input[type="radio"],input[type="checkbox"]').not(".prevent-icheck").each(function() {
      $this = jQuery(this);
      if(! $this.closest(".prevent-icheck").length ) {
        jQuery(this).iCheck({});
      }
    })
  };
})(newtheme);

$(function() {
  newtheme.initializeCustomCheckboxesAndRadios();
});