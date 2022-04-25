// a simple function to execute a callback, after the user has stopped typing for a specified amount of time
var typewatch = (function(){
  var timer = 0;
  return function(callback, ms){
    clearTimeout (timer);
    timer = setTimeout(callback, ms);
  }
})();

// Javascript for Autocomplete inputs
function Autocomplete(properties) {
  // Right now this is combining autocomplete and formset stuff...
  // Later separate the two

  var self = this;

  self.autocomplete_element = $(properties.autocomplete_element);
  self.input_element  = $(".input", self.autocomplete_element);
  self.url_path     = properties.url_path;
  self.selection_type = properties.selection_type || "no_action"; // other options: "formset", "inputvalue"

  self.max_show     = properties.max_show || 6;
  self.search_target  = $(properties.search_target);  // provide search element selector only if you want the option to direct search results to another element

  // selection_type=formset
  self.formset_prefix = properties.formset_prefix || "form";
  self.formset_show_selected_html = properties.formset_show_selected_html || true;    // boolean value
  self.record_template_url = self.autocomplete_element.attr("data-record-template-url");

  // selection_type = inputvalues, will replace the value of an input....
  self.inputvalue_selectors = self.autocomplete_element.attr("data-inputvalue-selectors") || "" //... with this selector

  self.lock_autocomplete = false;
  self.ajax_count = 0;

  function input_handler(event) {
    var keyword = self.input_element.val();
    self.search_target.slideUp(100);

    if (keyword == '' || self.lock_autocomplete == true) {
      $('.menu', self.autocomplete_element).remove();
    } else {
      self.ajax_count++;
      self.input_element.addClass("loading-right");
      $.ajax({
        "url": self.url_path,
        "data": { 
          "keyword":keyword
        },
        "success": function(data){

          if(self.lock_autocomplete == false) {
            $('.menu', self.autocomplete_element).remove();
            $(self.autocomplete_element).append(data);

            var menu = $('.menu', self.autocomplete_element);

            // don't position, leave it absolute where it is
            // menu.position({
            //   my: "left top",
            //   at: "left bottom",
            //   of: self.input_element,
            //   collision:"fit flip",
            //   within:menu.closest(".section, #content")
            // });
          }
          
        }
      }).done(function(){
        self.ajax_count--;
        if(self.ajax_count <= 0) self.input_element.removeClass("loading-right");
      });
    }
  }

  function search_handler(event) {
    var keyword = self.input_element.val();
    self.lock_autocomplete = true;
    self.ajax_count++;
    self.input_element.addClass("loading-right");
    if (keyword == '') {
      $('.menu',properties.autocomplete_element).remove();
    } else {
      self.input_element.addClass("loading-right");
      $.ajax({
        "url": self.url_path,
        "data": { 
          "keyword":keyword,
          "is_search":true
        },
        "success": function(data){
          $('.menu', self.autocomplete_element).remove();
          $(self.search_target).html(data);
          self.search_target.slideDown(100);
          self.input_element.removeClass("loading-right");
        }
      }).done(function(){
        self.ajax_count--;
        if(self.ajax_count <= 0) self.input_element.removeClass("loading-right");
      });
    }
  }

  function parse_formset_values(key_value_string) {
    // returns a dictionary of key value pairs
    // key_value_string is a string with format... "key0:value0;key1:value1;"
    var key_value_pairs = key_value_string.split(";");
    var key_value_dict  = {};
    for(var key in key_value_pairs) {
      var pair_array = key_value_pairs[key].split(":");
      if(pair_array.length == 2){
        key_value_dict[pair_array[0]] = pair_array[1];
      }
      else{
        // This key-value pair is not formatted correctly
      }
    }
    return key_value_dict;
  }

  // Uses formset.js
  function selection_formset_handler(event) {
    var selected_element = $(event.target).closest(".selectable");
    var values = parse_formset_values(selected_element.attr("data-values"));

    var new_record_element = FORMSETS[self.formset_prefix].add_item(values);

    if(self.record_template_url) {
      // option to load the new displayed record by supplanting values onto template url
      new_record_element.addClass("loading");
      $.get(self.record_template_url.supplant(values), function(data){
        new_record_element.append(data).removeClass("loading");
        $('.record').find('input[type="radio"],input[type="checkbox"]').iCheck({});
      });
      
    }else if(self.formset_show_selected_html) {
      // copies the displayed element from the selection
      new_record_element.append( selected_element.clone(true) );
      // $('input[type="radio"],input[type="checkbox"]').iCheck({});
    }

    $('.autocomplete .menu').remove()
  }

  function selection_inputvalue_handler(event) {
    var selected_element = $(event.target).closest(".selectable");
    var values = parse_formset_values(selected_element.attr("data-values")); // NOT ACUTALLY FORMSET, but a useful function to parse values
    var mapping = parse_formset_values(self.inputvalue_selectors); //dictionary mapping values to input css selectors

    for (var key in mapping) {
      var selector = mapping[key];
      var inputvalue = values[key] || "";
      $(selector).val(inputvalue).change();
    }

    $('.autocomplete .menu').remove()
  }

  // function formset_mark_for_deletion(record_index) {
  //  //Do this for forms that existed already
  //  var formset = $("#"+self.formset_prefix+"_formset");
  //  var record = (".record[data-index='"+record_index+"']", formset)
  //  var is_marked_for_deletion = record.hasClass('marked-for-deletion');
  //  if(is_marked_for_deletion) {
  //    $("[name='"+self.formset_prefix+"-"+record_index+"-DELETE']").remove();
  //    record.removeClass('marked-for-deletion');
  //  }else{
  //    var mark_for_deletion_input = $("<input type='hidden' name='"+self.formset_prefix+"-"+record_index+"-DELETE' />");
  //    formset.append(mark_for_deletion_input);
  //  }
    
  //  //do any css to show it's marked for deletion
  // }

  // function formset_remove(record_index) {
  //  //Do this for forms that hvae not been saved yet
  //  var formset = $("#"+self.formset_prefix+"_formset");
  //  var total_forms = $("[name='"+self.formset_prefix+"-TOTAL_FORMS']", formset).val();
  //  $(".record#id_"+self.formset_prefix+"-"+record_index, formset).remove();
  //  total_forms--;
  //  $("[name='"+self.formset_prefix+"-TOTAL_FORMS']", formset).val(total_forms);
  // }

  // function formset_delete_handler(event) {
  //  var record = $(event.target).closest('.record');
  //  var record_index = record.attr('data-index');
  //  var initial_forms = $("[name='"+self.formset_prefix+"-INITIAL_FORMS']", formset).val();
  //  if(record_index < initial_forms) {
  //    formset_mark_for_deletion(record_index);
  //  }else{
  //    formset_remove(record_index);
  //  }
  // }

  //EVENT HANDLERS

  self.input_element.on('input', function(){
    self.lock_autocomplete = false;
    typewatch(input_handler, 500);
  });

  self.input_element.keypress(function(event) {
    if (self.search_target && event.which == 13) {
      search_handler(event);
      return false;
    }
  });

  self.autocomplete_element.on('click', '.search-button', search_handler);
  self.autocomplete_element.on('click','.view-more', search_handler);

  self.search_target.on('click', '.clear-search', function(event){
    self.search_target.slideUp(100);
  });

  // for different handler types
  if(self.selection_type == 'formset'){
    // will add selected element to a formset...check other required data- params

    self.autocomplete_element.on('click', '.selectable', selection_formset_handler);

    if(self.search_target)
      self.search_target.on('click', '.selectable', selection_formset_handler);

  } else if (self.selection_type == 'inputvalue') {
    self.autocomplete_element.on('click', '.selectable', selection_inputvalue_handler);
    if(self.search_target)
      self.search_target.on('click', '.selectable', selection_inputvalue_handler);

  }else{
    // nothing should happen... this option is useful if you just want to link to some other page
  }

  //this is more of a formset thing
  // if(self.selection_type == 'formset')
  //  $('#'+self.formset_prefix+'_formset').on('click', '.delete', formset_delete_handler);

  return self;

}

$(function(){

  $(".autocomplete").each(function(index, value){
    var element = $(value);
    new Autocomplete({
      autocomplete_element:element,
      url_path:element.attr("data-url-path"),
      selection_type:element.attr("data-selection-type"),
      formset_prefix:element.attr("data-formset-prefix"),
      search_target:element.attr("data-search-target")
    });
  });

  $(document).on('click', function(event){
    //remove autocomplete if not clicked
    if (!$(event.target).closest('.autocomplete').length) {
        $('.autocomplete .menu').remove();
    }
  });
});














