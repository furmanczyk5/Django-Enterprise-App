var newtheme = newtheme || {};

//namespace just in case
(function( o ){

  o.conferenceFilterForm = function () {

    var $filterForm = $('#sort-facet-form'),
        $filters = $('.conference-search-filter-group').find('select'),
        $dates = $('.conference-search-date-group').find('input'),
        $filterFormDisabled = $('.sort-facet-form-disabled'),
        $dayAnchor = $('.conference-result-day-anchor'),
        $dayAnchorsHolder = $('.conference-day-anchors'),
        days = [];

    $filters.change(function () {
      submitForm();
    });

    $dates.change(function () {
      submitForm();
    });

    $dayAnchor.each(function(index) {
      $this = $(this);
      if (index === 0 & $this.attr('id') != "hide_skip_to") {
        $('<h4 class="conference-day-anchors-skip-to">Skip To</h4>').appendTo($dayAnchorsHolder);
      };
      //grab all
      // $this = $(this);
      $(
        '<a class="btn" href="#'
        + $this.attr('name')
        +'">'
        + $this.attr('title')
        + '</a>'
      ).appendTo($dayAnchorsHolder);

      // $dayAnchorsHolder
    });


    function submitForm() {
      $filterFormDisabled.addClass('active');
      $filterForm.submit();
    }
  }

})(newtheme);

$(function() {
  newtheme.conferenceFilterForm();
});