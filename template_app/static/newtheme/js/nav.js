var newtheme = newtheme || {};

//namespace just in case
(function( o ){
  o.mobileMenu = function(){
    var $headerMobileMenuToggle = $('.header-mobile-menu-toggle');

    var $mobileNavWrap = $('.mobile-menu-wrap'),
        $menu = $('.mobile-menu-list'),
        $childrenMenus = $('.mobile-menu-child'),
        $node = $menu.find('a'),
        depth = 0;


    $headerMobileMenuToggle.click(function () {
      var $this = $(this);

      if ($this.hasClass('active')) {
        $this.removeClass('active');
        $mobileNavWrap.removeClass('open');
        $node.off('click', handleClick); //detach
        //reset?
      } else {
        $this.addClass('active');
        $mobileNavWrap.addClass('open');
        $node.on('click', handleClick); //attach
        var offset = $mobileNavWrap.offset();
        //compute height minus header since the height is variable in menu children
        $mobileNavWrap.css('height', ($(document).height() - offset.top) + 'px');
      }

    });

    function resetMenu () {
      $headerMobileMenuToggle.removeClass('active');
      $mobileNavWrap.removeClass('open');
      $node.off('click', handleClick); //detach
      depth = 0;
      $menu.addClass('depth'+depth);
    }

    function handleClick (e) {
      var $child = $(this).siblings('.mobile-menu-child');
      // make sure it has children and menu is not moving
      if ($child.length > 0 && !$menu.hasClass('moving')) {

        e.preventDefault();

        if ($child.is(':hidden')) {
          // $menu.children('li').children('.mobile-menu-child').removeClass('open');
          $child.addClass('open');
        }
        moveForward();

      } else if ($(this).hasClass('mobile-menu-btn-back')) {
        e.preventDefault();
        moveBackward($(this));
      } else {
        return;
      }
    }

    function moveForward () {
      //can only move forward one at a time
      depth += 1;

      $menu.removeClass('depth'+(depth-1))
           .addClass('depth' + depth)
           .addClass('moving');
      //prevent double click moving twice, a little over css transition ms
      setTimeout(function(){ $menu.removeClass('moving') }, 850);
    }

    function moveBackward (obj) {

      var newDepth = obj.data('depth');

      $menu.removeClass('depth'+depth)
           .addClass('depth'+newDepth)
           .addClass('moving');
      //prevent double click moving twice, a little over css transition ms
      setTimeout(function(){
        $menu.removeClass('moving')
        if (newDepth == 0) {
          $menu.find('.mobile-menu-child').removeClass('open');
        } else {
          obj.parent().parent().removeClass('open').find('.mobile-menu-child').removeClass('open');
        }
      }, 850);
      depth = newDepth;

    }

  }

  o.mobileSearchBar = function () {

    $headerMobileSearchToggle = $('.header-mobile-search-toggle');

    $headerMobileSearchToggle.click(function () {
      $('.header-search-form-wrap').toggleClass('open');
    });
  }

  o.megaMenu = function () {

    var $navMegaMenuToggle = $(".nav-mega-menu-toggle"),
        $megaMenuWrap = $('.mega-menu-wrap'),
        $doc = $(document);

    $navMegaMenuToggle.click(function (e) {
      e.stopPropagation();
      e.preventDefault();

      var $this = $(e.currentTarget),
          megaMenuSection = $this.data('child');

      if($this.hasClass('active')) {

        $this.removeClass('active')
             .parent().parent().removeClass('active');

        $('#'+megaMenuSection).removeClass('open');
        $doc.off('click', closeMegaMenus); //detach event

      } else {
        $navMegaMenuToggle.removeClass('active')
             .parent().parent().removeClass('active');
        $this.addClass('active')
             .parent().parent().addClass('active');

        $('#'+megaMenuSection).addClass('open').siblings().removeClass('open');
        $doc.on('click', closeMegaMenus); //attach event to check to close

      }

    });

    function closeMegaMenus (e) {

      // not a nav toggle and not a mega menu
      if (!$navMegaMenuToggle.is(e.target)
      && $megaMenuWrap.has(e.target).length === 0) {
        $navMegaMenuToggle.removeClass('active')
             .parent().parent().removeClass('active');
        $megaMenuWrap.children('.mega-menu-section').removeClass('open');
        $doc.off('click', closeMegaMenus); //detach this event

      } else {
        return;
      }

    }
  }

})(newtheme);

$(function() {
    newtheme.mobileMenu();
    newtheme.mobileSearchBar();
    newtheme.megaMenu();
});