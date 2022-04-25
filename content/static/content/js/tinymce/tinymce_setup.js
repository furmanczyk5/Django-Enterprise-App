tinyMCE.init({
    
    // see http://www.tinymce.com/wiki.php/Configuration
    selector: 'textarea[data-wysiwyg]',
    plugins: "link code image preview visualblocks",
    toolbar: "undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | link unlink | image | code visualblocks preview",
    paste_auto_cleanup_on_paste : true,
    valid_styles: {},
    invalid_elements:"script",

    height:300,
    resize:true,

    link_list: [
        {title: 'Planning.org', value: 'https://www.planning.org'}
    ],

    setup: function (editor) {
        editor.on('change', function () {
            editor.save();
        });
    },

    // content_css: '../content/css/style.css'
    
});

