// This js is for conditionally including js and css only when needed

function DetectResource(jquery_selector, resource_array) {

	var self = this;
	self.selector = jquery_selector;
	self.resource_array = resource_array;

	function loadCSS_checked(href) {
		var isCSSIncluded = $("link[href='"+href+"']").length > 0;
		if( !isCSSIncluded ) {
			$('head').append('<link rel="stylesheet" href="'+href+'" type="text/css" media="screen" />');
		}
	}

	function loadJS_checked(src) {
		var isJSIncluded = $("script[src='"+src+"']").length > 0;
		if( !isJSIncluded ) {
			$('head').append('<script type="text/javascript" src="'+src+'"></script>');
		}
	}

	self.isSelectorPresent = function() {
		return $(self.selector).length > 0;
	}

	self.includeResource = function(resource_path) {

		var css_pattern = /.css$/;
		var js_pattern = /.js$/;

		if( css_pattern.test(resource_path) ) {
			loadCSS_checked( resource_path );
		} else if ( js_pattern.test(resource_path) ) {
			loadJS_checked( resource_path );
		} else {
			console.log("Detect Resource Error: '" + resource_path + "' is not a js or css file");
		}
	}

	self.detect = function() {

		if( self.isSelectorPresent() ) {
			for(var i = 0; i < self.resource_array.length; i++) {
				self.includeResource( resource_array[i] );
			}
		}
	}

	return self;
}


//////////////////////////////////////////////////////////////////////////////////
// THIS IS WHERE WE DEFINE THE RESOURCES THAT WE WANT TO INCLUDE CONDITIONALLY ///
//////////////////////////////////////////////////////////////////////////////////
var DETECT_RESOURCES = [
	new DetectResource( '[data-wysiwyg]', 							['/static/content/js/tinymce/tinymce.min.js', '/static/content/js/tinymce/tinymce_setup.js'] ),			// WYSIWYG EDITOR
	new DetectResource( 'a[rel^=lightbox], area[rel^=lightbox]', 	['/static/lightbox/js/lightbox.js', '/static/lightbox/css/lightbox.css'] ),							// LIGHTBOX SLIDESHOWS
	new DetectResource( '.upnext-widget', 							['/static/content/js/conference/upnext.js', '/static/content/css/conference/upnext.css'] ),				// CONFERENCE UPNEXT WIDGET
	new DetectResource( '.tooltip, .tooltip-bio', 					['/static/tooltipster/css/tooltipster.css',
																		// '/static/tooltipster/css/themes/tooltipster-shadow.css',
																	 '/static/tooltipster/js/jquery.tooltipster.min.js',
																     '/static/tooltipster/js/tooltipster_setup.js' 	] ),		// TOOLTIP JQUERY PLUGIN
	new DetectResource( '.formset',									['/static/ui/forms/js/formset.js']),
	new DetectResource( '.autocomplete',  							['/static/content/js/jquery-ui.min.js','/static/autocomplete/js/autocomplete.js']),
	new DetectResource( '.selectchain',								['/static/ui/forms/js/selectchain.js']),
	new DetectResource( '.planning-datetime-widget',				['/static/rome/rome.min.css', '/static/rome/rome_custom.css','/static/rome/rome.min.js', '/static/rome/rome_setup.js']),
	new DetectResource( '.wordcounter',								['/static/ui/forms/js/wordcount.js', '/static/ui/forms/css/wordcount.css'])
] 

$(function(){

	$.each( DETECT_RESOURCES, function( index, value ) {
		value.detect();
	});

});







