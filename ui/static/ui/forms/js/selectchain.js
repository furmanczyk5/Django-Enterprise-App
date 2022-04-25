// select widget
/*
	WORKING PARTS:
	- server side application to return select codes and values when called to
		-
	- front end javascript application
		- detects changes in select
		- makes calls to server to get choices for selected value

		- works with select-facade class
*/

// LOTS OF THINGS WORK THIS WAY...CAN PROBABLY USE INHERITANCE
var planning_selectchain = {
	
	application_root : "/ui/selectable/options",

	eventHandler : function(event) {
		planning_selectchain.run(event.target);
	},

	run : function(selector) {

		var commander 	= $(selector);
		var isformset	= commander.is("[data-selectchain-isformset]"); 	// Then target should be the field name
		var follower 	= isformset ? planning_selectchain.get_follower_formset(commander) : $(commander.attr("data-selectchain-target"));		// The select that depends on the commander value
		var mode		= commander.attr("data-selectchain-mode");			// Will determine the type of results to return
		var value 		= commander.val();									// used to filter the results returned
		
		var encoded_value = encodeURIComponent(value);
		var url			= planning_selectchain.application_root + "/" + mode + "/?value=" + encoded_value;
		
		var loader = follower.closest('.select-facade') || follower;
		function loadHandler(){
			follower.change();
			loader.removeClass('loading');
			// check if the follower has more than just the empty selected element
			// and add disabled attribute if not
			if (follower.children().length <= 1) {
				var parent = follower.parent();  // the <span> select facade
				// add the "optional" help-block
				parent.after('<div id="job-info-state-select" class="help-block">optional</div>')
			}
		}

		$('#job-info-state-select').detach();
		loader.addClass('loading');
		follower.removeAttr('disabled');
		var html_data 	= follower.load(url, loadHandler);
	},

	get_follower_formset : function(commander){
		var follower_name = commander.attr("data-selectchain-target");
		var commander_id  = commander.attr("id");
		return $("#" + commander_id.replace(/(?!.*-).*/, follower_name) ) // MASTERFUL REGEX
	}, 

	register_delegated : function() {
		$(document).on('change', 'select.selectchain', planning_selectchain.eventHandler);
	}

};


$(function(){
	planning_selectchain.register_delegated();
});