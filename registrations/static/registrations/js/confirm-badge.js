$(function(){

	var $badge_name_input = $("#confirm_badge_form [name='badge_name']");
	var $badge_name_display = $("#badge_preview .badge-name");
	
	function mirror_changes($input_element, $copycat_element) {
		$input_element.on("input", function(event){
			var input_value = $input_element.val();
			$copycat_element.html(input_value);
		});
	}

	var $badge_name_input = $("#confirm_badge_form [name='badge_name']");
	var $badge_name_display = $("#badge_preview .badge-name");

	var $badge_company_input = $("#confirm_badge_form [name='badge_company']");
	var $badge_company_display = $("#badge_preview .company");

	var $badge_location_input = $("#confirm_badge_form [name='badge_location']");
	var $badge_location_display = $("#badge_preview .location");

	mirror_changes($badge_name_input, $badge_name_display);
	mirror_changes($badge_company_input, $badge_company_display);
	mirror_changes($badge_location_input, $badge_location_display);

});