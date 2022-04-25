var newtheme = newtheme || {};

//namespace just in case
(function( o ){

  o.formValidators  = [];

  o.initializeValidation = function () {
    //Add validation code here
    var $allForms = jQuery(".validate-form");

    $allForms.each(function () {
      var $form = jQuery(this);

      var formValidator = $form.validate({
        onfocusout: false, //prevents validating form fields on blur. Only validates on submit.
        errorElement: 'p',
        errorClass: 'form-error-client',
        errorContainer: [],
        ignore: [], //Don't ignore hidden inputs: http://stackoverflow.com/a/8565769
        highlight: function(element, errorClass) {
          var $element = $(element);
          var $group = $element.closest('.form-group');
          $group.addClass('has-error');
        },
        unhighlight: function (element, errorClass) {
          var $element = $(element);
          var $group = $element.closest('.form-group');
          $group.removeClass('has-error');
        },
        errorPlacement: function($error, $element) {
          var $group,
            $existingErrorContainer,
            $newErrorContainer;

          $group = $element.closest('.form-group');

          if($group.length === 0) {
            return; //No form group!
          }

          $existingErrorContainer = $group.find('.form-error');

          if($existingErrorContainer.length) {
            $existingErrorContainer.append($error);
          }
          else
          {
            $newErrorContainer = $('<div>', {
              'class': 'form-error'
            });
            $group.append($newErrorContainer);
            $newErrorContainer.append($error);
          }

        }
      });

      o.formValidators.push(formValidator);

      /* /////////////////
      // VALIDATION FIELDS
      // Below are rules for individual fields, applied by putting a class of
      // ".validate-field-*" on the affected form control.
      ///////////////////// */

      //Password Rules
      $form.find('.validate-field-password').each(function() {
        jQuery(this).rules("add", {
          required: true,
          minlength: 8,
          maxlength: 16,
          messages: {
            minlength: "Password must be 8-16 characters in length",
            maxlength: "Password must be 8-16 characters in length"
          }
        });
      });

      //Confirm Password
      $form.find('.validate-field-password-confirm').each(function() {
        jQuery(this).rules("add", {
          equalTo: '.validate-field-password'
        });
      });

      //Confirm Email
      $form.find('.validate-field-email-confirm').each(function() {
        jQuery(this).rules("add", {
          equalTo: '.validate-field-email', //I hope this is scoped to a single form only, will require more testing.
          email: false
        });
      });

      //Confirm Secondary Email
      $form.find('.validate-field-secondary-email-confirm').each(function() {
        jQuery(this).rules("add", {
          equalTo: '.validate-field-secondary-email', //I hope this is scoped to a single form only, will require more testing.
          email: false
        });
      });

    }); //end $forms.each()

  };

  o.cancelValidation = function(){
    for(var i = 0; i < o.formValidators.length; i++) {
      o.formValidators[i].destroy();
    }
    o.formValidators.splice(0, o.formValidators.length); //clear this array
  };

})(newtheme);

$(function() {
  newtheme.initializeValidation();
});
