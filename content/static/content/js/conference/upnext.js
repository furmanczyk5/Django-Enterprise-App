Upnext = (function(){

	this.timeIntervalHandler = function() {
		$.get("/conference/upnext/")
			.done(ajaxHandler)
	};

	this.ajaxHandler = function(data) {

		var parsedHTML = $(data);

		$oldlist = $(".record", ".upnext-widget");
		$newlist = $(".record", parsedHTML);

		var is_changed = !compareListByIds($oldlist, $newlist);
		$widget = $(".upnext-widget")

		if(is_changed){
			$widget.fadeOut(200, function() {
				$widget.html(data);
				$widget.fadeIn(200);
			});
		}else{
			$widget.html(data);
		}
	};

	this.compareListByIds = function(oldlist, newlist) {
		if(oldlist.length != newlist.length) {
			return false
		}else{
			for(var i = 0; i < oldlist.length; i++){
				if( $(oldlist[i]).attr("data-master") != $(newlist[i]).attr("data-master")) {
					return false;
				}
			}
			return true
		}
	};

	return this;

})()

$(function(){


	Upnext.timeIntervalHandler();
	setInterval(Upnext.timeIntervalHandler, 60000);

});