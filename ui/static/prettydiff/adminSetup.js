$(function(){
	$("a.prettydiff-compare-to-published").click(function(event){
		var url = $(event.target).attr("href");
		$.get(url, function(data){
			var dataProcessor = CKEDITOR.instances.ckeditor_admin.dataProcessor;
			var source_html = dataProcessor.toHtml(data.content.text);
			var source_dataformat = dataProcessor.toDataFormat(source_html);
			var text_editor_html = CKEDITOR.instances.ckeditor_admin.getData();
			var prettydiff_options = {
		        source: source_dataformat,
		        diff  : text_editor_html,
		        lang  : "text",
		        diffview : "inline"
		    };
			var prettydiff_output = prettydiff(prettydiff_options);
			var $prettydiff_output = $(prettydiff_output)
			// var prettydiff_style = $prettydiff_output.filter("style").prop('outerHTML');
			var prettydiff_report = $prettydiff_output.filter("div.contentarea").prop('outerHTML');
			// var prettydiff_js = $prettydiff_output.filter("script").prop('outerHTML');
			var html = "<div id='prettydiff' class='white'>"+prettydiff_report+"</div>";
			PlanningModal.show({"html":html});
		});
		return false;
	});

	$(document, "select#colorScheme").change(function(event){
		var value = $(event.target).val();
		var the_class = value.toLowerCase();
		var the_prettydiff = $("#prettydiff");
		the_prettydiff.removeClass("white canvas shadow");
		the_prettydiff.addClass(the_class);
	})
});
