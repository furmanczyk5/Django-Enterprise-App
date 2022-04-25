CKEDITOR.plugins.add("planning_media", {
	icons:'planning_media',
	init: function(editor){
		editor.addCommand('planning_media', new CKEDITOR.dialogCommand('planning_media_Dialog') );
		CKEDITOR.dialog.add( 'planning_media_Dialog', this.path + 'dialogs/planning_media.js' );
		editor.ui.addButton( 'planning_media', {
		    label: 'Insert Planning Media',
		    command: 'planning_media',
		    toolbar: 'insert'
		});

		if ( editor.contextMenu ) {
		    editor.addMenuGroup( 'planning_media_Group' );
		    editor.addMenuItem( 'planning_media_Item', {
		        label: 'Edit Planning Media',
		        icon: this.path + 'icons/planning_media.png',
		        command: 'planning_media',
		        group: 'planning_media_Group'
		    });
		    editor.contextMenu.addListener( function( element ) {
		        var ascendantplanningmedia = element.getAscendant( function(el){
		        	var has_plannningmedia_class = el && el.hasClass && el.hasClass("planning-media");
		        	var is_img_or_link = el.getName ? ["img","a"].indexOf(el.getName()) > -1 : false;
		    		return has_plannningmedia_class || is_img_or_link;
		    	}, true );
		        if ( ascendantplanningmedia ) {
		            return { planning_media_Item: CKEDITOR.TRISTATE_OFF };
		        }
		    });
		}
	}
});