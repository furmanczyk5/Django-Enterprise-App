/* Since our web content team thinks we're still in the 90s and they love both
pasting from Microsoft Word and clicking toolbar buttons to apply styles (with some
 detours into Dreamweaver every now and then for good measure), we need this
silliness below to disable applying inline styles only when pasting from Word.

Thankfully someone already figured this out, because CKEditor docs are not great:
https://codepen.io/mlewand/pen/oeaZrV

 */

$(document).ready(function() {
  CKEDITOR.on('instanceReady', function(ev) {

    ev.editor.on('afterPasteFromWord', function(evt) {
      var filter = evt.editor.filter.clone(),
          fragment = CKEDITOR.htmlParser.fragment.fromHtml(evt.data.dataValue),
          writer = new CKEDITOR.htmlParser.basicWriter();

      filter.allow('*[*]{*}');
      filter.disallow('*[style]{*}');
      filter.disallow('span');
      filter.applyTo(fragment);
      fragment.writeHtml(writer);
      evt.data.dataValue = writer.getHtml();
    })
  });

});
