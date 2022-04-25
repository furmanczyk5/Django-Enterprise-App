CKEDITOR.plugins.add("planning_language", {
	requires: 'richcombo',
    beforeInit: function( editor ) {
        editor.lang.format.tag_p = 'Body Copy';
    }
});