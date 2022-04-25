$(function(){

  	$("input[name$='-contact']").change(function(){
  		var contact_id = $(this).val();
  		$peaker_contact_display = $("#speaker_contact_display");
  		$peaker_contact_display.css("display","block");
  		$peaker_contact_display.addClass("loading");
  		$peaker_contact_display.load("/events/submissions/speaker_formset/display_record/" + contact_id + "/", function(){
  			$peaker_contact_display.removeClass("loading");
  		})
  	});

});