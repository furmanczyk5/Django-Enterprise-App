$(function(){

	$(".planning-datetime-widget").each(function(){
		var showTime = $(this).attr("data-show-time")
		rome(this, options={
			"autoClose":"time",
			"timeFormat":"hh:mm a",
			"time": showTime != null ? showTime == 'true' : true,
			"timeInterval":900 // 15 min (in seconds)
		});
	});
	
});