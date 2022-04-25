CKEDITOR.plugins.add("planning_shortcode", {
	icons:'planning-shortcode',
	init: function(editor){
		editor.addCommand('planning_shortcode', new CKEDITOR.dialogCommand('planning_shortcode_Dialog') );
		CKEDITOR.dialog.add( 'planning_shortcode_Dialog', this.path + 'dialogs/planning_shortcode.js' );
		editor.ui.addButton( 'planning_shortcode', {
		    label: 'Insert Planning Shortcode',
		    command: 'planning_shortcode',
			icon:this.path + 'icons/planning-shortcode.png',
		    toolbar: 'insert'
		});

		if ( editor.contextMenu ) {
		    editor.addMenuGroup( 'planning_shortcode_Group' );
		    editor.addMenuItem( 'planning_shortcode_Item', {
		        label: 'Edit Planning Shortcode',
		        icon: this.path + 'icons/planning-shortcode.png',
		        command: 'planning_shortcode',
		        group: 'planning_shortcode_Group'
		    });
		    editor.contextMenu.addListener( function( element ) { 
		    	var ascendantshortcode = element.getAscendant( function(el){
		    		return el && el.getAttribute && el.getAttribute("data-planning-shortcode");
		    	}, true );
		        if ( ascendantshortcode ) {
		            return { planning_shortcode_Item: CKEDITOR.TRISTATE_OFF };
		        }
		    });
		}
	}
});