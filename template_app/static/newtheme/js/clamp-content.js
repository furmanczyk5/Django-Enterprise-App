/* /////////////////////////////
// CLAMP
///////////////////////////// */

var newtheme = newtheme || {};

(function( o ){

  o.applyClamps = function () {

    jQuery('.clamp-1').each(function(){
      var elem = this;
      $clamp(this, {clamp: 1});
    });

    jQuery('.clamp-2, .book-card .book-title').each(function(){
      var elem = this;
      $clamp(this, {clamp: 2});
    });

    jQuery('.clamp-3').each(function(){
      var elem = this;
      $clamp(this, {clamp: 3});
    });

    jQuery('.clamp-4').each(function(){
      var elem = this;
      $clamp(this, {clamp: 4});
    });

  };

})(newtheme);

$(function() {
  newtheme.applyClamps();
});