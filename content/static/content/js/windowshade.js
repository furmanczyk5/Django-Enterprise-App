function registerWindowShades() {

	function makeHandler(properties) {
		var switcher = properties.switcher;
		var source_type = properties.source_type;
		var trackclick = properties.trackclick;
		function handler(event){
			var source = $(event.target).closest(source_type);
			var target_selector = source.attr('data-target');
			var target = $(target_selector);
			if(target[0]){
				if(trackclick && !source.hasClass('clickedLast')){
					event.preventDefault();
					$('.clickedLast').removeClass('clickedLast');
					source.addClass('clickedLast');
				}else{
					target.toggleClass('hidden', switcher);	
				}
			}
		}
		return handler;
	}

	// mobile hover window shades turn into click windowshades

	$(document).on('click', '.windowshade', makeHandler({source_type:'.windowshade'}));
	$(document).on({
		'mouseenter':makeHandler({source_type:'.windowshade-hover', switcher:false}),
		'mouseleave':makeHandler({source_type:'.windowshade-hover', switcher:true})
	},'.windowshade-hover');
	$(document).on('click','.windowshade-mobile-hover',makeHandler({source_type:'.windowshade-mobile-hover', trackclick:true}));

	// make transitions possible
	// add handlers for target element, when using hover
};

function registerWindowShade_tree() {
	/*
	Built so that tables can be turned into a document tree
	No need for hover window shades here (this has more rules, so anything to make this simpler)
	*/

	function handler(event) {
		var source = $(event.target).closest('.windowshade_tree');
		var switcher = source.is('.windowshade_tree.open ');
		source.toggleClass('closed', switcher);
		source.toggleClass('open', !switcher);

		var target_selector = source.attr('data-target');
		var target = $(target_selector);

		if(!switcher) { //opening
			target.filter("[data-hidden-by='"+target_selector+"']").removeAttr('data-hidden-by');
			target = target.not('[data-hidden-by]' + target_selector);
		}else{ //closing
			target.not('[data-hidden-by]' + target_selector).attr('data-hidden-by',target_selector);
		}

		target.toggleClass('hidden',switcher)

	}

	$('.windowshade_tree').addClass('closed') // initialize all tree nodes to closed

	$(document).on('click', '.windowshade_tree', handler);
	$(document).on('touchstart', '.windowshade_tree', handler);

	// make transitions possible

}

$(function(){
	registerWindowShades();
	registerWindowShade_tree();
});



