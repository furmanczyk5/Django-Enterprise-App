var newtheme = newtheme || {};

//namespace just in case
(function( o ){

    o.initializeSocialSharing = function () {
        //Instead of loading AddThis' javascript on every single page, we will only lazy-load it if we detect that it is needed.
        var $addThisElements = jQuery('.addthis_sharing_toolbox');

        if($addThisElements.length > 0) {
            // console.log('AddThis dependency detected, loading addthis.js')
            var s = document.createElement('script');
            s.type = 'text/javascript';
            s.async = true;
            s.src = '//s7.addthis.com/js/300/addthis_widget.js#pubid=americanplanningassociation';
            var x = document.getElementsByTagName('script')[0];
            x.parentNode.insertBefore(s, x);
        }
    }

})(newtheme);

$(function() {
  newtheme.initializeSocialSharing();
});
