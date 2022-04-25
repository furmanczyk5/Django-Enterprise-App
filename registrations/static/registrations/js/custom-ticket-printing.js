$(function(){

	var update_fields_display = function(event) {
		var $ticket_template = $(event.target);
		var value = $ticket_template.val();
		switch(value){
			case "registrations/tickets/layouts/CONFERENCE-BADGE.html":
				$("fieldset[data-ticket-fields='badge']").show();
				$("fieldset[data-ticket-fields='session']").hide();
				$("fieldset[data-ticket-fields='nonbadge']").hide();
				break;
			case "registrations/tickets/layouts/CONFERENCE-ACTIVITY.html":
				$("fieldset[data-ticket-fields='badge']").hide();
				$("fieldset[data-ticket-fields='session']").show();
				$("fieldset[data-ticket-fields='nonbadge']").show();
				break;
			default:
				$("fieldset[data-ticket-fields='badge']").hide();
				$("fieldset[data-ticket-fields='session']").hide();
				$("fieldset[data-ticket-fields='nonbadge']").show();
				break;
		}	
	}

	var $ticket_template = $("select[name='ticket_template'");

	$ticket_template.on("change", update_fields_display);
	$ticket_template.trigger("change");

});