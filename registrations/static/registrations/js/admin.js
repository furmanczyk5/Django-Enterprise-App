function watchTask(task_id) {

	$("li.grp-changelist-actions").hide();
	$("li.print-address-labels").show();
	$(".print-address-labels-download").hide()
	$(".print-address-labels-loading").show();
	$(".print-address-labels-message").html("");
	$(".print-address-labels-message").show();

	var taskwatcher = setInterval(function(){
		$.get("/registrations/task/poll/", {"task_id":task_id})
			.done(function(data){
				console.log(data);
  				if(["RECEIVED", "PENDING", "PROGRESS"].indexOf(data.status) < 0) {

  					$("li.grp-changelist-actions").show();
					$(".print-address-labels-loading").hide();

  					clearInterval(taskwatcher);

  					if(data.status == "SUCCESS") {
  						console.log("SUCCESS!");
  						$(".print-address-labels-download").attr("href", "/registrations/task/pdf/?task_id=" + task_id)
  						$(".print-address-labels-download").show();
  						$(".print-address-labels-message").hide();
  					}else{
  						console.log("NOPE!");
  						$(".print-address-labels-download").hide();
  						$(".print-address-labels-message").html("Failed");
  					}

  				} else {
  					$(".print-address-labels-message").html(data.message || "Pending");
  				}

  				// otherwise, it's still going
			});
	},1000);
}

function showError(task_id) {

}

$(function(){

	$("form#grp-changelist-form button[type='submit']").click(function(event){
		$(this.form).data('clicked', this.value);
	});

	$("form#grp-changelist-form").submit(function(event){
		var $form = $(event.target);
		var action_button_val = $form.data('clicked');
		var action_val = $("select[name='action']").val();
		$form.removeData('clicked');
		if(action_button_val != null && action_val == "print_address_labels") {
			// submit via ajax, watch progress

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
				});

			return false;
		}
		
	});

	$("li.grp-changelist-actions").after(
		"<li class='print-address-labels' style='display:none;'>" +
			"<img src='/static/content/image/ajax-loader.svg' class='print-address-labels-loading' style='display:none;vertical-align:middle;'/>" +
			"<span class='print-address-labels-message' style='display:none;vertical-align:middle;'></span>" +
			"<a href='' class='grp-button print-address-labels-download' style='display:none;vertical-align:middle;'>Download Address Labels</a>" +
		"</li>");

});