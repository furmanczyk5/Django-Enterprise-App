// if(apa && apa.ui){ 
// 	apa.ui.scroll = {

// 		scroll_properties:{}




// 	}
// }

$(function(){
	$(document).on({
		'touchstart':function(event){

			var origin_touch 	= event.originalEvent.touches[0] || event.originalEvent.changedTouches[0];
			var origin_page_y   = origin_touch.pageY;
			var scroller 		= $(event.target).closest('.scroll');
			var scroller_wrap	=scroller.closest('.scroll-wrap');
			var origin_top		= scroller.position().top;

			scroller.attr('top', origin_top + 'px');

			var is_scroll = false;

			//just need to keep track of momentum somehow

			//DON'T FORGET ABOUT WIDE SCREEN VIEW

			/*
			
			1. Store the original touch position in a variable. Using a closure, the handler functions will have access to this variable

			2. Set the scroller top to whatever it is currently, this stops any previous scrolling

			3. Define touchmove and touchend handlers

			4. set event handlers for those events

			*/

			function touchmoveHandler(event){

				event.preventDefault();

				this_touch 	= event.originalEvent.touches[0] || event.originalEvent.changedTouches[0];
				this_page_y = this_touch.pageY;

				scroller.css('top', origin_top + this_page_y - origin_page_y);

			}

			function touchendHandler(event){

				container_height = scroller_wrap.innerHeight();
				scroller_height = scroller.outerHeight();
				current_top = scroller.position().top;

				//check bourdaries HERE
				if(current_top > 0 || scroller_height <= container_height){
					scroller.animate({'top':0}, 200);
				}else if(current_top < container_height - scroller_height){
					scroller.animate({'top':container_height-scroller_height}, 200);
				}

				scroller.off();
			}

			scroller.on({
				'touchmove' : touchmoveHandler,
				'touchend'  : touchendHandler
			});
		}
	},'.scroll-wrap .scroll');

	//treat all taps as if they are clicks, location.
	// $(document).on('tap', function(event){
		
	// 	console.log(event.isDefaultPrevented());
	// 	if(event.isDefaultPrevented()){
	// 		var redirect = $(event.target).clostest('a').attr('href');
	// 		window.location.replace(redirect);
	// 	}
		
	// });

});



