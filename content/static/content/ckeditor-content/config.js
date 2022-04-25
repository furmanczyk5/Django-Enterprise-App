/**
 * @license Copyright (c) 2003-2019, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {

  // %REMOVE_START%
  // The configuration options below are needed when running CKEditor from source files.
  config.plugins = 'dialogui,dialog,about,basicstyles,notification,button,toolbar,clipboard,enterkey,entities,floatingspace,wysiwygarea,indent,indentlist,fakeobjects,link,list,undo,pastetools,pastefromword,pasteFromGoogleDoc';
  config.skin = 'minimalist';
  config.allowedContent = false;
  config.disallowedContent = 'script;*[style]{*}';

  // %REMOVE_END%

  // Define changes to default configuration here.
  // For complete reference see:
  // https://ckeditor.com/docs/ckeditor4/latest/api/CKEDITOR_config.html

  // FLAGGED FOR REFACTORING: PLANNING MAG CKEDITOR
  // IS THIS WHERE CSS IS LOADED FOR CONTENT ADMIN? APPARENTLY NOT? I SAW NO CHANGE
  config.contentsCss = [
    CKEDITOR.getUrl("../css/icomoon/style.css"),
    CKEDITOR.getUrl("../css/newtheme_style.css"),
  ];

  config.bodyClass = "container content-wrap";

  // The toolbar groups arrangement, optimized for a single toolbar row.
  config.toolbarGroups = [
    { name: 'document',    groups: [ 'mode', 'document', 'doctools' ] },
    { name: 'clipboard',   groups: [ 'clipboard', 'undo' ] },
    { name: 'editing',     groups: [ 'find', 'selection', 'spellchecker' ] },
    { name: 'forms' },
    { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
    { name: 'paragraph',   groups: [ 'list', 'indent', 'blocks', 'align', 'bidi' ] },
    { name: 'links' },
    // { name: 'insert' },
    // { name: 'styles' },
    // { name: 'colors' },
    // { name: 'tools' },
    // { name: 'others' },
    // { name: 'about' }
  ];

  // The default plugins included in the basic setup define some buttons that
  // are not needed in a basic editor. They are removed here.
  config.removeButtons = 'Cut,Copy,Paste,Undo,Redo,Anchor,Underline,Strike,Subscript,Superscript';

  // Dialog windows are also simplified.
  config.removeDialogTabs = 'link:target;link:advanced';
};
