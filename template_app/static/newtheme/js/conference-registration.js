/* ////////////////////////
// Conference Registration Toggles (new conf theme)
//////////////////////// */

(function(){

  function registerRadioFacade() {

    function handler(event) {

      var target = $(event.target);
      var targetFacade = target.closest(".radio-facade");
      var targetInput = targetFacade.find("input:radio");
      var radioName = targetInput.attr("name");
      var closestForm = targetInput.closest("form");
      var allradiosSelector = closestForm.length > 0 ? $("[name='"+radioName+"']", closestForm) : $("[name='"+radioName+"']");

      allradiosSelector.prop("checked", false);
      allradiosSelector.closest(".radio-facade").removeClass("selected");
      targetFacade.addClass("selected");
      targetInput.prop("checked", true);
      targetInput.change();
    }

    $(document).on("click", ".radio-facade", handler);
  }

  registerRadioFacade();

})();
