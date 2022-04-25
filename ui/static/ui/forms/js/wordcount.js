var planning_wordcount = {

	eventHandler : function(event) {
		planning_wordcount.run(event.target);
	},

	run : function(selector) {
		var target = $(selector)
		var text = target.val() || "";
		var words = text.match(/\S+/g) || [] // /(\d+(\.|,)|(\w+('|-)*))+/g (to account for hyphenated words, appostrophies, decimals, and words like 1,000,000)
		var wordcount = words.length;
		$(".wordcounter-display-wrap").remove();
		target.after('<span class="wordcounter-display-wrap"><span class="wordcounter-display">'+wordcount+' words</span></span>');
	},

	register_all : function() {
		$('input.wordcounter, textarea.wordcounter').on('input', planning_wordcount.eventHandler);
	}
}

$(function(){
	planning_wordcount.register_all();
});

/*

  position: absolute;
  background-color: green;
  color: white;
  padding: 2px;
  font-size: 0.8em;
  display: block;
  right: 0px;
  bottom: 0px;
  opacity: 0.8;
*/