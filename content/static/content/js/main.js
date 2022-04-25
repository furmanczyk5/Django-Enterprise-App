String.prototype.trim = function() {
	return this.replace(/^\s+|\s+$/gm,'');
}

String.prototype.trim_char = function(char_string) {
	// broken
	var regex_expression = new RegExp("/^[" + char_string + "]+|[" + char_string + "]+$/gm");
	return this.replace(regex_expression,'');
}

String.prototype.supplant = function (o) {
    return this.replace(/{([^{}]*)}/g,
        function (a, b) {
            var r = o[b];
            return typeof r === 'string' || typeof r === 'number' ? r : a;
        }
    );
};

// a simple function to execute a callback, after the user has stopped typing for a specified amount of time
var typewatch = (function(){
  var timer = 0;
  return function(callback, ms){
    clearTimeout (timer);
    timer = setTimeout(callback, ms);
  }  
})();

if(!apa){ 
	var apa = { 
		BASE_URL : 'http://localhost:8000/',
	}
}

apa.ui = {

	changeClass : function(properties) {
		var selector = properties.selector;
		var addThis = properties.addClass;
		var removeThis = properties.removeClass;
		$(selector).addClass(addThis);
		$(selector).removeClass(removeThis);
	},

	toggleClass : function(properties){
		var selector = properties.selector;
		var toggleClass = properties.toggleClass;
		var _switch = properties.switch;
		$(selector).toggleClass(toggleClass, _switch);
	}

}

//////////////////////////////////////
// matchMedia for responsive design //
//////////////////////////////////////
if(window.matchMedia){
	apa.matchMedia = {};
	apa.matchMedia.queries = {
		width_480: {
			query:window.matchMedia('(max-width:480px)'),
			matchHandler:function() {
				apa.ui.changeClass({'selector':'.windowshade-hover', 'addClass':'windowshade-mobile-hover', 'removeClass':'windowshade-hover'});
			},
			mismatchHandler:function(){
				apa.ui.changeClass({'selector':'.windowshade-mobile-hover', 'addClass':'windowshade-hover', 'removeClass':'windowshade-mobile-hover'});
			}
		},
	}

	apa.matchMedia.registerAll = function() {

		for(x in apa.matchMedia.queries){
			var mq = apa.matchMedia.queries[x];
			function handler(match){
				if(match.matches){
					mq.matchHandler();
				}else{
					mq.mismatchHandler();
				}
			};
			handler(mq.query);
			mq.query.addListener(handler);
		}
	};
}


function registerFormSubmit() {

	function handler(event) {
		target = $(event.target).closest('.action');
		if(target[0]) {
			target.addClass('loading');
		}
	};

	$(document).on('submit', 'form', handler);

};

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

function registerToggleClassController(){

	function handler(event){
		var target_selector = $(event.target).closest('.toggleClassController').attr('data-target');
		var toggle_class = $(event.target).closest('.toggleClassController').attr('data-class');
		$(target_selector).toggleClass(toggle_class);
	}

	$(document).on('click','.toggleClassController', handler);

};

function registerScrollingBanner() {

	var scroller = $(window);

	var banner = $('#banner');
	var banner_image = $('#banner .paralax-banner');

	if(banner_image[0]){

		var b_h, b_t, i_h;

		function setBannerGeometry() {
			b_h = banner.innerHeight();
			b_t = banner.position().top;
			i_h = banner_image.height();
		};

		function handler(event) {

			setBannerGeometry();

			var s_t = scroller.scrollTop();
			var img_top = (i_h - b_h) * s_t / (b_h + b_t);

			if(b_h + b_t - s_t >= 0 && s_t >= 0) {
				var img_top = (b_h - i_h) * (1 - (s_t / (b_h + b_t)));
				// var img_top = (b_h - i_h) * (s_t / (b_h + b_t));
				if(img_top <= 0) {
					banner_image.css('top', img_top + 'px');
				}
			}

		};

		// initial position, only if using first img_top eqn
		handler();
		
		return scroller.on('scroll resize',handler);

	} else {
		return false;
	}
	
};

function registerStickyHandler(properties) {

	// properties: 	scroller_selector (listen to scroll event on this element, default to window)
	//				indicator_selector (add class to body when the top of this is out of view)
	//				class_name (class to add to body as needed )

	var indicator = $(properties.indicator_selector);
	var scroller = $(properties.scroller_selector || window);

	function handler(event){
		
		var needs_fixed = indicator.position().top - scroller.scrollTop() < 0;
		var is_fixed = $('body').hasClass(properties.class_name);

		if(needs_fixed && !is_fixed){
			$('body').addClass(properties.class_name);
		}else if(!needs_fixed && is_fixed){
			$('body').removeClass(properties.class_name);
		}
	};

	if(indicator[0] && scroller[0]){
		return scroller.on('scroll',handler);
	}else{
		return false;
	}
};

function registerWindowScrollHandler() {

	var scroller = $(window);

	function handler(event){

		var scroll_top = scroller.scrollTop();

		$('.windowScrollEventTarget').each(function(){

			var element = $(this);
			var indicator = element.attr('data-indicator') ? $(element.attr('data-indicator')) : $(this).closest('.shell');
			var target = $(element.attr('data-target') || this);
			var class_name = element.attr('data-className');

			var needs_fixed = indicator.offset().top - scroller.scrollTop() - 32 < 0; //need way to check for offset hardcoded as 32 right now
			var is_fixed = target.hasClass(class_name);

			if(needs_fixed && !is_fixed){
				target.addClass(class_name);
			}else if(!needs_fixed && is_fixed){
				target.removeClass(class_name);
			}
		});

	};

	scroller.on('scroll', handler);
};

function registerSelectFacade() {

	function set_display(target_selector) {

		var select_input = $(target_selector);
		var selected_option = $('option:selected',select_input);
		var select_facade = select_input.closest('.select-facade');
		var facade_new_text = selected_option.text() || select_facade.attr("data-empty-text") || "Nothing Selected";

		$('.facade-text',select_facade).text(facade_new_text);

		return selected_option
	}

	function handler(event) {
		var selected_option = set_display(event.target);

		if (selected_option.is('[data-href]')) {
			window.location.href = selected_option.attr('data-href');
		}
	};

	// initial values for select facade
	$('.select-facade select').each(function(){
		set_display(this);
	});

	$(document).on('change', '.select-facade select', handler);
	
};

function registerCheckboxFacade() {

	function handler(event) {
		var target = $(event.target);
		if(!target.is("input:checkbox")){
			var checkboxFacade = target.closest(".checkbox-facade");
			var checkbox = $("input:checkbox", checkboxFacade);
			checkbox.prop("checked", !checkbox.prop("checked"));
			checkbox.change();
		}
	};

	$(document).on("click", ".checkbox-facade", handler);

}

function registerTabRadio() {



	 function handler(event) {
	 	var target = $(event.target);
	 	var tab = target.closest(".tab-radio");
	 	tab.closest(".tabs").find(".tab-radio").removeClass("selected");
		if(target.is(":checked")){
			tab.addClass("selected");
		}else{
			tab.removeClass("selected");
		}
	 }

	 $(".tab-radio input[type='radio']:checked").closest(".tab-radio").addClass("selected");
	 $(document).on("change", ".tab-radio input[type='radio']", handler)
}

function registerRadioFacade() {

	function handler(event) {

		var target = $(event.target);
		var targetFacade = target.closest(".radio-facade");
		var targetInput = targetFacade.find("input:radio");
		var radioName = targetInput.attr("name");
		var closestForm = targetInput.closest("form");
		var allradiosSelector = closestForm.length > 0 ? $("[name='"+radioName+"']", closestForm) : $("[name='"+radioName+"']");

		allradiosSelector.prop("checked", false);
		allradiosSelector.closest(".radio-facade").removeClass("selected");
		targetFacade.addClass("selected");
		targetInput.prop("checked", true);
		targetInput.change();
	}

	$(document).on("click", ".radio-facade", handler);
}

function registerSubmitOnChange() {

	function handler(event) {
		var target = $(event.target);
		target.closest("form").submit();
	}

	$(document).on("change", "form.submit-on-change input, form.submit-on-change select", handler)
}


// handler is executed when the DOM is fully loaded
$(function(){

	// detectLightbox();
	// detectUpnext();

	// //clicking anywhere on the page
	$(document).on('click', function(event){
		//removeClass from clickedLasts that were not just clicked 
		if(!$(event.target).closest('.clickedLast').length){
			$('.clickedLast').removeClass('clickedLast');
		}
	})

	registerStickyHandler({
		indicator_selector : '#navigation-shell',
		class_name : 'sticky-navigation'
	});

	// registerStickyHandler({
	// 	indicator_selector : '#content',
	// 	class_name : 'sticky-column'
	// });

	//registerAutocompletes();
	registerScrollingBanner();
	registerWindowShades();
	registerToggleClassController();
	registerFormSubmit();
	registerWindowScrollHandler();
	registerSelectFacade();
	registerCheckboxFacade();
	registerRadioFacade();
	registerTabRadio();
	registerSubmitOnChange();

	if(window.matchMedia){
		apa.matchMedia.registerAll();
	}

});
