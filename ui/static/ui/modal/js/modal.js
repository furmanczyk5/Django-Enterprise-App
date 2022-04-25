var ClipBoard, PlanningModal;

$(function(){

	ClipBoard = function() {

		var self = this;


		if (!$("#clipboard")) {
			$("body").append("<div id='clipboard'></div>");
		}

		this.cut = function(selector, from) {
			from = from || "#clipboard"
			self.stored_content = $(selector, from).remove();
			return self.stored_content;
		}

		this.copy = function(selector, from){
			from = from || "#clipboard"
			self.stored_content = $(selector, from).append("");
			return self.stored_content;
		}

		this.paste = function(selector) {
			if(selector) {
				$(selector).html(self.stored_content)
			}
			return self.stored_content;
		}

		this.store = function() {
			$("#clipboard").append(self.stored_content);
		}

		return this;
	}();

	PlanningModal = function() {
		// Only supporting url and selector, later ability to pass html?

		var self = this;
		this.is_visible = false;

		this.show = function(options, complete){

			var url = options.url;
			var html = options.html;
			var selector = options.selector; // uses the clipboard

			$("body").append("<div class='screen body-screen' style='display:none'></div>");
			$("body").append("<div class='planning-modal loading' style='display:none'></div>");

			var body_screen = $("body .body-screen");
			var modal = $("body .planning-modal")

			var close_save = url ? "false" : "true";

			var modal_header_element = modal.append("<div class='planning-modal-header'><a class='right icon-close' href='javascript:PlanningModal.close("+close_save+")'></a></div>").find(".planning-modal-header");
			var modal_content_element = modal.append("<div class='planning-modal-content'></div>").find(".planning-modal-content");
			var modal_footer_element = modal.append("<div class='planning-modal-footer'></div>").find(".planning-modal-footer");

			if(url) {
				modal_content_element.load(url, function(){
					modal.removeClass("loading");
				});
			}else if(html) {
				$(modal_content_element).html(html);
				modal.removeClass("loading");
			}else{
				var modal_content = $("#clipboard " + selector)
				$("form", modal_content).each(function(){this.reset()}); // reset any forms
				ClipBoard.cut(selector);
				ClipBoard.paste(modal_content_element);
				modal.removeClass("loading");
			}

			modal.css({"opacity":0,"display":"block"});
			body_screen.css({"opacity":0,"display":"block"});
			self.is_visible = true;
			self.adjust();
			
			body_screen.fadeTo(100, 0.7, function(){ 
				modal.fadeTo(100, 1, self.adjust);
			});

			if(complete) complete();
		}

		this.close = function(save, complete){

			var body_screen = $("body .body-screen");
			var modal = $("body .planning-modal");

			modal.fadeOut(100, function(){

				if(save){
					ClipBoard.cut(modal.find(".planning-modal-content").html(), "body");
					ClipBoard.store();
				}

				$(this).remove();
				body_screen.fadeOut(100, function(){
					$(this).remove();
					self.is_visible = false;
				});

			});

			if(complete) complete();
		}

		this.adjust = function() {
			if(self.is_visible) {
				var body_screen = $("body .body-screen");
				var modal = $("body .planning-modal");
				if(modal.length) {
					modal.position({
					  my: "center center",
					  at: "center center",
					  of: body_screen,
					  collision:"fit fit",
					  within:body_screen
					});
				}	
			}	
		}

		$(window).resize(self.adjust);

		return this;

	}();

	// $(docuemnt, ".show-modal").on("click", function(event){
	// 	var target = $(event.target);
	// 	var url = target.attr("data-url") || null;
	// 	var selector = target.attr("data-selector") || null;

	// });

});
