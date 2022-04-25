function tooltipster_setup() {

	$('.tooltip',document).not('.tooltipstered').tooltipster({
		maxWidth:500
	});
	$('.tooltip-bio',document).not('.tooltipstered').tooltipster({
			maxWidth:500,
			delay:0,
			trigger:'click'
			// theme:'tooltipster-shadow'
		});
}

function tooltipster_watcher() {
	$(document).on('mouseenter','.tooltip, .tooltip-bio', function(event) {
		var tooltip_element = $(this);

		if( !tooltip_element.hasClass('tooltipstered') ) {
			tooltipster_setup();
		}
	});
}	

$(function(){

	tooltipster_setup();
	tooltipster_watcher();

})