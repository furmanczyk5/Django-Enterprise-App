$(function(){

	$(document).on("change", ".selectmultipletagswidget select", function(event){
		var target = $(event.target);
		var selected_value = target.val();
		if(selected_value){
			var widget_closest = target.closest(".selectmultipletagswidget");
			var checkbox_target = widget_closest.find(".tag-checkbox input[value="+selected_value+"]");
			checkbox_target.prop("checked", true);
		}
		target.val("");
	});

});