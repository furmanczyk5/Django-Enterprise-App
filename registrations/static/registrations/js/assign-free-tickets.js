$(function(){

	function watchTask(task_id) {
		$("#assign-free-tickets-form-ready").hide();
		$("#assign-free-tickets-revoke").attr("data-taskId", task_id);
		$("#assign-free-tickets-form-progress").show();
		var taskwatcher = setInterval(function(){
			$.get("/registrations/task/poll/", {"task_id":task_id})
				.done(function(data){
					console.log(data);
	  				if(["RECEIVED", "PENDING", "PROGRESS"].indexOf(data.status) < 0) {
	  					$("#assign-free-tickets-form-progress").hide();
	  					$("#assign-free-tickets-form-ready").show();
	  					$(".assign-free-tickets-message").text(data.message);
	  					$("#assign-free-tickets-progress").css("width","0%");
	  					clearInterval(taskwatcher);

	  					if(data.status == "SUCCESS") {
	  						console.log("SUCCESS!");
	  					}else{
	  						console.log("NOPE!");
	  					}

	  				}else{
	  					$("#assign-free-tickets-progress").css("width",(data.complete*100)+"%");
	  					$(".assign-free-tickets-message").text(data.message);
	  				}
  				});
		},1000);
	}

	function showError(task_id) {

	}

	$("form#assign-free-tickets-form").on("submit", function() {
		var $form = $(this);
		$.post($form.attr('action'), $form.serialize())
			.done(function(data){
				if(data.success){
					watchTask(data.task_id);
				}else{
					showError(data.errors);
				}
				console.log("DONE");
				console.log(data);
				// Also check if server caught an error
			})
			.fail(function(data){
				console.log("FAIL");
				console.log(data);
			})
			.always(function(data){
				console.log("ALWAYS");
				console.log(data);
			})
		return false;
	});

	$("#assign-free-tickets-revoke").on("click", function(event){
		var $this = $(event.target);
		var task_id = $this.attr("data-taskId");
		$.get("/registrations/task/revoke/", {"task_id":task_id});
	});

});





