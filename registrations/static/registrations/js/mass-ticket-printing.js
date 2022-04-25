$(function(){

	var default_page_options = {
		"sato": {
			"page_margin_top":0.0785,
			"page_margin_bottom":0.0785,
			"page_margin_left":0.0785,
			"page_margin_right":0.0785
		},
		"letter": {
			"page_margin_top":0.25,
			"page_margin_bottom":1.75,
			"page_margin_left":0.1875,
			"page_margin_right":0.1875
		},
		"letter_time_correction": {
			"page_margin_top":0.25,
			"page_margin_bottom":0.75,
			"page_margin_left":0.1875,
			"page_margin_right":0.1875
		}
	}

	$("[name=paper_size]").on("change", function(){
		var $paper_size = $(this);
		var paper_size = $paper_size.val();
		var $page_margin_top = $("[name=page_margin_top]");
		var $page_margin_bottom = $("[name=page_margin_bottom]");
		var $page_margin_left = $("[name=page_margin_left]");
		var $page_margin_right = $("[name=page_margin_right]");

		$page_margin_top.val(default_page_options[paper_size]["page_margin_top"]);
		$page_margin_bottom.val(default_page_options[paper_size]["page_margin_bottom"]);
		$page_margin_left.val(default_page_options[paper_size]["page_margin_left"]);
		$page_margin_right.val(default_page_options[paper_size]["page_margin_right"]);

	});

	function showFormMessage(errors) {
		$("#mass-ticket-printing-form-progress").hide();
		$("#mass-ticket-printing-message").html(errors);
		$("#mass-ticket-printing-form-ready").show();
	}

	function addProgressBar(task_name, task_id) {
		var progress_bar_string = "" +
			"<div class='task-progress' data-taskId='"+task_id+"'>" +
				"<div style='float:right;'><a href='javascript:;' class='task-revoke'>Cancel</a></div>" +
				"<div><b>"+task_name+": </b><span class='task-message'></span></div>" +
				"<div class='task-progressbar'>" +
					"<div style='width:0%;' class='task-progressbar-progress'></div>" +
				"</div>"+
				"<div class='task-result' style='display:none;'>" +
					"<a target='_blank' href='/registrations/task/pdf/?task_id="+ task_id +"'>download tickets pdf</a>" +
				"</div>" +
			"</div>"
		$("#mass-ticket-printing-form-progress").append(progress_bar_string);
	}

	function showResult(task_id) {
		var $task_progress = $(".task-progress[data-taskId='"+task_id+"']");
		$(".task-revoke, .task-progressbar", $task_progress).hide();
		$(".task-result", $task_progress).show();
	}

	function showError(task_id) {
		var $task_progress = $(".task-progress[data-taskId='"+task_id+"']");
		$(".task-revoke, .task-progressbar", $task_progress).hide();
		$(".task-result", $task_progress).hide();
	}

	function checkComplete(){
		if($(".task-progressbar:visible").length == 0) {
			// then everything is finished running, allow to submit another form
			$("#mass-ticket-printing-form-ready").show();
		}
	}

	function revokeAll(){
		// should do this if leaving the page?

		for(element in $(".task-progress")) {
			var task_id = $(element).closest(".task-progress").attr("data-taskId");
			$.get("/registrations/task/revoke/", {"task_id":task_id});
		}
		
	}

	function watchTask(task_id, interval) {

		interval = interval || 8000;
		var $task_progress = $(".task-progress[data-taskId='"+task_id+"']");
		var $task_message = $(".task-message", $task_progress);
		var $task_progressbar_progress = $(".task-progressbar-progress", $task_progress);

		$(".task-revoke, .task-progressbar", $task_progress).show();
		$(".task-result", $task_progress).hide();

		$task_progressbar_progress.css("width","0%");
		
		var taskwatcher = setInterval(function(){
			$.get("/registrations/task/poll/", {"task_id":task_id})
				.done(function(data){
					console.log(data);
	  				if(["RECEIVED", "PENDING", "PROGRESS"].indexOf(data.status) < 0) {
	  					
	  					clearInterval(taskwatcher);
	  					$task_message.text(data.message);

	  					if(data.status == "SUCCESS") {
	  						showResult(task_id);
	  					} else {
	  						showError(task_id);
	  					}

	  					checkComplete();

	  				}else{
	  					$task_progressbar_progress.css("width",(data.complete*100)+"%");
	  					$task_message.text(data.message);

	  					if(data.status == "PROGRESS" && interval >= 8000) {
	  						clearInterval(taskwatcher);
	  						watchTask(task_id, 2000)
	  					}
	  				}
  				});
		}, interval);
	}

	// ADAPT TO WORK FOR MULTIPLE TASKS, response from post will return multiple task ids
	$("form#mass-ticket-printing-form").on("submit", function() {
		var $form = $(this);
		$("#mass-ticket-printing-form-ready").hide();
		$(".task-progress").remove();
		$("#mass-ticket-printing-form-progress").show();
		$.post($form.attr('action'), $form.serialize())
			.done(function(data){
				if(data.success){
					$("#mass-ticket-printing-message").html("");
					for(var i = 0; i < data.tasks.length; i++){
						var task = data.tasks[i]
						addProgressBar(task.name, task.task_id);
						watchTask(task.task_id);
					}
				}else{
					showFormMessage(data.errors);
				}
				console.log("DONE");
				console.log(data);
				// Also check if server caught an error
			})
			.fail(function(data){
				console.log("FAIL");
				console.log(data);
				showFormMessage("Server Error");
			})
			.always(function(data){
				console.log("ALWAYS");
				console.log(data);
			})
		return false;
	});

	$(".task-revoke", "#mass-ticket-printing-form-progress").on("click", function(event){
		var $this = $(event.target);
		var task_id = $this.closest(".task-progress").attr("data-taskId");
		$.get("/registrations/task/revoke/", {"task_id":task_id});	
	});

});





