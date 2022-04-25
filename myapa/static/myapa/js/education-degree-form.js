
function EducationDegreeForm(container_selector) {

  var self = this;

  container_selector = container_selector || document;
  self.$container = $(container_selector);
  self.prefix = self.$container.attr("data-prefix") || "";

  self.$school = $("select[name='"+self.prefix+"school']", self.$container);
  self.$degreeProgram = $("select[name='"+self.prefix+"degree_program']", self.$container);
  self.$degreeType = $("select[name='"+self.prefix+"degree_type_choice']", self.$container);
  self.$degreeLevel = $("select[name='"+self.prefix+"level']", self.$container);
  self.$isCurrent = $("input[type='checkbox'][name='"+self.prefix+"is_current']", self.$container);
  self.$isComplete = $("input[type='checkbox'][name='"+self.prefix+"complete']", self.$container);

  self.$degreeProgramContainer = $(".degree-program-other", self.$container);

  self.$otherFieldsContainer = $(".other-school-fields", self.$container);
  self.$schoolOtherContainer = $(".school-other", self.$container);
  self.$degreeTypeOtherContainer = $(".degreetype-other", self.$container);
  self.$degreeLevelOtherContainer= $(".degreelevel-other", self.$container);

  self.showHideFields = function() {
    var school_val = self.$school.val();
    var degreeProgram_val = self.$degreeProgram.val();
    var degreeType_val = self.$degreeType.val();
    var degreeLevel_val = self.$degreeLevel.val();

    // show/hide degree program and school other
    if (school_val == "OTHER") {
      self.$degreeProgramContainer.slideUp();
      self.$schoolOtherContainer.slideDown();
    }else{
      self.$degreeProgramContainer.slideDown();
      self.$schoolOtherContainer.slideUp();
    }

    // show/hide other fields
    if (school_val == "OTHER" || degreeProgram_val == "OTHER") {
      self.$otherFieldsContainer.slideDown();
    }else{
      self.$otherFieldsContainer.slideUp();
    }

    // show/hide degreetype other
    if(degreeType_val == "OTHER") {
      self.$degreeTypeOtherContainer.slideDown();
    }else{
      self.$degreeTypeOtherContainer.slideUp();
    }

    // show/hide degree level other
    if(degreeLevel_val == "N") {
      self.$degreeLevelOtherContainer.slideDown();
    }else{
      self.$degreeLevelOtherContainer.slideUp();
    }
  }

  self.uncheckIsComplete = function() {
    self.$isComplete.iCheck('uncheck');
  }

  self.uncheckIsCurrent = function() {
    self.$isCurrent.iCheck('uncheck');
  }

  function watchFields() {
    self.$school.on("change", self.showHideFields);
    self.$degreeProgram.on("change", self.showHideFields);
    self.$degreeType.on("change", self.showHideFields);
    self.$degreeLevel.on("change", self.showHideFields);
    self.$degreeLevel.on("change", self.showHideFields);
    self.$isCurrent.on("ifChecked", self.uncheckIsComplete); // "ifToggeled" used with icheck checkboxes
    self.$isComplete.on("ifChecked", self.uncheckIsCurrent);
  }

  self.showHideFields();
  watchFields();

  return self;
}
