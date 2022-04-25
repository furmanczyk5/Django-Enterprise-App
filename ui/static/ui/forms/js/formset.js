// Use class="formset" to identify formsets
// Use data-prefix="<PREFIX>" to identify specific formsets

function Formset(formset_prefix) {
	var self = this;

	this.formset_prefix = formset_prefix;
	this.formset 	= $("#"+self.formset_prefix+"_formset");
	this.empty_form = $(".empty_form", this.formset);
	this.total_element 	= $("[name='"+this.formset_prefix+"-TOTAL_FORMS']", formset);
	this.total 			= total_element.val();

	this.add_item = function(values, oncomplete) {

		var selected_forms_array = $( self.empty_form.html().replace(/__prefix__/g, self.total) );
		var new_record_id = "id_"+self.formset_prefix+"-"+self.total;
		formset.append("<div class='record' id='"+new_record_id+"' data-index='"+self.total+"'></div>");
		var new_record_element = $("#"+new_record_id);

		for(var i = 0; i < selected_forms_array.length; i++) {
			new_record_element.append(selected_forms_array[i]);
		}

		for(var key in values) {
			var key_input = $("[name='"+self.formset_prefix+"-"+self.total+"-"+key+"']", formset);
			key_input.val(values[key]);
		}

		// set total after adding
		self.total++;
		self.total_element.val(self.total);

		if (this.oncomplete) this.oncomplete(values);

		return new_record_element
	}

	return this;
}

var FORMSETS = {}

$(function(){

	$(".formset").each(function() {
		var prefix = $(this).attr("data-prefix")
		FORMSETS[prefix] = Formset(prefix)
	});

});