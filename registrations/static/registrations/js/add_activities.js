$(function(){

	// FILTER TICKETS
	function filter_activities() {
		var active_filters = [];
		$("a.filter_controller.active, input.filter_controller:checked").each(function(i, e){
			active_filters.push("["+$(e).attr("data-filter-code")+"]");
		});
		$(".activity").addClass("hidden");
		$(".activity"+active_filters.join("")).removeClass("hidden");
	};	

	$("a.filter_controller").on("click", function(e){
		$("a.filter_controller").removeClass("active");
		$(e).addClass("active");
		filter_activities();
	});

	$("input.filter_controller").on("change", filter_activities);

	// REFRESH CART
	function refresh_cart() {
		var the_cart = $(".registration-the_cart");
		var loading_element = the_cart.closest(".action");
		loading_element.addClass("loading");
		the_cart.load("/store/include/cart/", function(){
			loading_element.removeClass("loading");
			//registerRemoveFromCart();
		});
	};

	function refresh_ticket_widget(element, callback) {
		var widget = $(element).closest(".registration_add-ticket-widget")
		var master_id = widget.attr("data-master-id");
		$(widget).find("form").addClass("loading")
		widget.load("/registrations/includes/ticket-buttons/"+master_id+"/", callback);
	};

	// ADD TO CART
	$(document).on("submit", "form.registration-add_to_cart", function(e){
		var the_form = $(e.target);
		the_form.addClass("loading")
		the_form.children('button').attr("disabled", "disabled")
		$.post("/store/cart/update/json/", the_form.serialize(), function(data) {
			refresh_cart();
			refresh_ticket_widget(the_form);
		});

		return false
	});

	// REMOVE FROM CART
	function registerRemoveFromCart() {
		$(document).on("submit", "form.remove-from-cart", function(e){
			var the_form = $(e.target);
			the_form.closest("td").addClass("loading")

			$.post("/store/cart/remove/json/", the_form.serialize(), function(data) {
				var master_id = the_form.attr("data-master-id");
				var ticket_widget = $(".registration_add-ticket-widget[data-master-id="+master_id+"]");
				the_form.closest("td").removeClass("loading");
				$(".registration-the_cart").closest(".action").addClass("loading");
				//refresh_cart();
				//refresh_ticket_widget(ticket_widget);
				location.reload();
			});

			return false;
		});
	};
	registerRemoveFromCart();

});