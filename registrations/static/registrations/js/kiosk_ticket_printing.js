$(function(){

	var action_in_progress = false;
	var application_root_path = window.location.pathname;

	function refresh_attendees() {
		$(".application-workspace").addClass("loading");
		$("#print-tickets-form").load(application_root_path + "refresh/", function() {
			$(".application-workspace").removeClass("loading");
		})
	}

	// $("a#print-tickets-button").click( function(event){
	// 	$("form#print-tickets-form").submit();
	// });

	// $("a#dismiss-attendee-button").click(function(event){
	// 	$(".application-workspace").addClass("loading");
	// 	$.post(application_root_path + "dismiss/", $("form#print-tickets-form").serialize(), function(data){
	// 		refresh_attendees();
	// 	});
	// });

	$("a#refresh-attendees-button").click(function(event){
		refresh_attendees();
	});

});
