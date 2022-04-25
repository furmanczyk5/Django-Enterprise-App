if(!apa){
	var apa = {}
}

apa.admin = {

	//needed to make ajax posts
	csrftoken : $.cookie('csrftoken'),

	// properties: formSelector, success
	submit : function(properties){
		var form_selector = properties.form_selector;
		// var data = properties.data;
		// var url = properties.url;
		var success = properties.success || function(){};
		// var failure = properties.failure;
		// var redirect = properties.redirect;

		var form = form_selector ? $(form_selector) : undefined;
		if(form && form.prop('tagName') !== 'FORM'){
			form = form.closest('form');
		}

		var url = form.attr("action") || location.pathname;

		// for the text editor
		if(CKEDITOR){
			for ( i in CKEDITOR.instances ) {
				CKEDITOR.instances[i].updateElement();
			}
		}

		if(form[0]){
			$.post(url, form.serialize() + '&_popup=true', success)
				.fail(function(){ alert("failed to save"); });
		}

	},

	publish_prod : function(properties){
		var content_id = properties.content_id;

		$.post('/content/publish/'+content_id+'/', function(){ location.reload() })
			.fail(function(){ alert("failed"); });

	}

};

//for making ajax posts
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", apa.admin.csrftoken);
        }
    }
});

// $(function(jq){

// 	var $ = jq;

// })($ || django.jQuery)
