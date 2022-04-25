/*
CKEditor Config for the Django admin
 */

CKEDITOR.editorConfig = function (config) {

  if (typeof page_template !== "undefined" && page_template === "PAGE") {
    config.contentsCss = [
      CKEDITOR.getUrl("../content/css/icomoon/style.css"),
      CKEDITOR.getUrl("../content/css/style.css"),
      CKEDITOR.getUrl("../content/css/editor_shortcodes.css"),
      CKEDITOR.getUrl("../content/css/editor_custom_conference.css")];

    config.bodyClass = "content-left"
  } else {
    config.contentsCss = [
      CKEDITOR.getUrl("../content/css/icomoon/style.css"),
      CKEDITOR.getUrl("../content/css/newtheme_style.css"),
      CKEDITOR.getUrl("../content/css/editor_shortcodes.css"),
      CKEDITOR.getUrl("../content/css/editor_custom.css")];

    config.bodyClass = "container content-wrap"
  }

  config.disallowedContent = "script";
  config.allowedContent = true;
  config.stylesSet = "planning_styles";
  config.format_tags = "p;h2;h3;h4;h5;h6";
  config.extraPlugins = "planning_media,planning_shortcode,planning_language,lite";
  config.templates_replaceContent = false;
  config.templates_files = ['/static/ckeditor/templates/planning_templates.js?v=1.0'];

  // For the LoopIndex LITE Plugin - Track Changes on CKEditor
  var lite = config.lite || {};
  config.lite = lite;
  config.lite.includes = ["lite-includes.min.js", "plugin.js"];
  // config.lite.userName = current_user;
  config.lite.isTracking = false; // disable tracking by default for initial content migration... may opt to make it default to true later.

  config.toolbar = [
    {name: 'tools', items: ['Maximize', 'ShowBlocks']},
    {name: 'print', items: ['Print']},
    {name: 'document', items: ['Source']},
    {name: 'clipboard', items: ['Cut', 'Copy', 'PasteFromWord', '-', 'Undo', 'Redo']},
    {name: 'editing', items: ['Find', 'Replace', 'SelectAll', 'Scayt']},
    {name: 'links', items: ['Link', 'Unlink', 'Anchor']},
    //{ name: 'lite', items: [LITE.Commands.TOGGLE_TRACKING, LITE.Commands.TOGGLE_SHOW, LITE.Commands.ACCEPT_ONE, LITE.Commands.REJECT_ONE, LITE.Commands.ACCEPT_ALL, LITE.Commands.REJECT_ALL] },
    '/',
    {name: 'basicstyles', items: ['Bold', 'Italic', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat']},
    {name: 'paragraph', items: ['NumberedList', 'BulletedList', '-', '-', 'Outdent', 'Indent']},
    {name: 'styles', items: ['Styles', 'Format', 'Templates']},
    {name: 'insert', items: ['planning_media', 'planning_shortcode', 'HorizontalRule', 'SpecialChar']}
  ];


  // config.toolbarGroups = [
  //     { name: 'document', groups: [ 'tools', 'mode'] },
  //     { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
  //     { name: 'editing', groups: [ 'find', 'selection', 'spellchecker', 'editing' ] },
  //     '/',
  //     { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
  //     { name: 'paragraph', groups: [ 'list', 'blocks', 'align', 'bidi', 'paragraph' ] },
  //     { name: 'links', groups: [ 'links' ] },
  //     { name: 'insert', groups: [ 'insert' ] },
  //     '/',
  //     { name: 'styles', groups: [ 'styles' ] },
  //     // { name: 'tools', groups: [ 'tools' ] },
  //     { name: 'others', groups: [ 'others' ] },
  //     { name: 'about', groups: [ 'about' ] },
  //     { name: 'lite' }, //, groups: [LITE.Commands.TOGGLE_SHOW, LITE.Commands.ACCEPT_ALL, LITE.Commands.REJECT_ALL] },
  // ];

  config.removeButtons = 'About,TextColor,BGColor,Font,FontSize,Smiley,Flash,Language,BidiRtl,BidiLtr,Save,NewPage';
  config.height = 400;
  // config.toolbarGroups = [
  //     { name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
  //     { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
  //     { name: 'editing', groups: [ 'find', 'selection', 'spellchecker', 'editing' ] },
  //     '/',
  //     { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
  //     { name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi', 'paragraph' ] },
  //     { name: 'links', groups: [ 'links' ] },
  //     { name: 'insert', groups: [ 'insert' ] },
  //     '/',
  //     { name: 'styles', groups: [ 'styles' ] },
  //     { name: 'colors', groups: [ 'colors' ] },
  //     { name: 'tools', groups: [ 'tools' ] },
  //     { name: 'others', groups: [ 'others' ] },
  //     { name: 'about', groups: [ 'about' ] },
  //     { name: 'lite' }, //, groups: [LITE.Commands.TOGGLE_SHOW, LITE.Commands.ACCEPT_ALL, LITE.Commands.REJECT_ALL] },
  // ];

};

// this allows block level links for divs (valid for html5 but ckeditor by defuault doesnt allow then)
// add similar lines to this to allow <a> tags to wrap other elements
CKEDITOR.dtd.a.div = 1;

CKEDITOR.on('instanceReady', function (ev) {
  var blockTags = ['div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'li', 'blockquote', 'ul', 'ol',
    'table', 'thead', 'tbody', 'tfoot', 'td', 'th'];

  var w = ev.editor.dataProcessor.writer;
  for (var i = 0; i < blockTags.length; i++) {
    w.setRules(blockTags[i], {
      indent: true,
      breakBeforeOpen: true,
      breakAfterOpen: false,
      breakBeforeClose: false,
      breakAfterClose: false
    });
  }
});
