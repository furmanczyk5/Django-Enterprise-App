$(function(){

	$('#provider_logo_edit').on('click', function(){
		$('#provider_logo_action').slideDown(100);
		$('#provider_logo_display').slideUp(100);
	});

	$('#provider_logo_cancel').on('click', function(){
		$('#provider_logo_action').slideUp(100);
		$('#provider_logo_display').slideDown(100);
	});

	$('#provider_bio_edit').on('click', function(){
		$('#provider_bio_action').slideDown(100);
		$('#provider_bio_display').slideUp(100);
	});

	$('#provider_bio_cancel').on('click', function(){
		$('#provider_bio_action').slideUp(100);
		$('#provider_bio_display').slideDown(100);
	});

	$('.see-event-reviews').on('click', function(){
		var the_button = $(this);
		var event_master_id = the_button.attr('id').match(/(?!.*-)\d+/)[0];
		var event_reviews = $("#event-reviews-"+event_master_id);
		the_button.addClass("loading");
		event_reviews.load("/cm/provider/event/"+event_master_id+"/comments/", function(){
			the_button.removeClass("loading");
			event_reviews.slideDown(100);
		});
	});

	$(document).on('click', '.close-event-reviews', function(){
		var event_reviews = $(this).closest(".event-reviews");
		event_reviews.slideUp(100);
	});

});