var newtheme = newtheme || {};

//namespace just in case
(function( o ){

  o.filterSortControl = function () {

    var $facetTagBtn = $('.btn-facet-tag'),
        $facetTagBtnSelected = $('.btn-facet-tag-selected'),
        $facetTags = $('.facet-tag'),
        $sortFacetForm = $('#sort-facet-form'),
        $sortSelect = $('#sort-select').find('select'),
        $btnClearTags = $('.btn-clear-tags'),
        $sortFacetFormDisabled = $('.sort-facet-form-disabled');

    $sortSelect.change(function () {
      $sortFacetForm.submit();
    });

    $('.sort_dropdown').find('a').click(function (e) {
      e.preventDefault();
      var $this = $(this),
          option = $this.data('option');
      console.log($sortSelect.val());
      console.log(option);
      if($sortSelect.val() != option) {
        $sortSelect.val(option).change();
      } else {
        return;
      }

    });

    $facetTagBtn.click(function (e) {
      e.preventDefault();
      var $this = $(this);
          tag = $this.data('tag');

      $('#'+tag).prop('checked', true);
      submitForm();
    });

    $facetTagBtnSelected.click(function(e) {
      e.preventDefault();
      var $this = $(this);
          tag = $this.data('tag');

      $('#'+tag).prop('checked', false);
      submitForm();
    });

    $btnClearTags.click(function (e) {
      $facetTags.prop('checked', false);
      submitForm();
    });

    function submitForm() {
      $sortFacetFormDisabled.addClass('active');
      $sortFacetForm.submit();
    }
  }

})(newtheme);

$(function() {
  newtheme.filterSortControl();
});