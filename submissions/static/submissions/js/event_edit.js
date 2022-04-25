// function get_speaker_display_record(values) {
// 	$.get("/submissions/speaker_formset/display_record/"+values.contact+"/", function(data){
// 		element = $("input[value='"+values.contact+"']").closest(".record");
// 		element.append(data);
// 	});
// }

$(function(){

	$(document).on("submit", "form.anonymous-contact-create-form", function(event){

		var form = $(event.target);
		$.post(form.attr("action"), form.serialize(), function(data){

			console.log($.type(data));

			if($.type(data) === "string") {
				$(".planning-modal-content").html(data)
				PlanningModal.adjust();
			}else{
				var new_record_element = FORMSETS[self.formset_prefix].add_item({"contact":data.id});
				new_record_element.addClass("loading");
				$.get("/events/submissions/speaker_formset/display_record/{contact}/".supplant({"contact":data.id}), function(get_data){
					new_record_element.append(get_data).removeClass("loading");
				});
				PlanningModal.close();
			}

		});

		return false;

	});

});