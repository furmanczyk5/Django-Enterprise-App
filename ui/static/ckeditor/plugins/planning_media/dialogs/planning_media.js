CKEDITOR.dialog.add( 'planning_media_Dialog', function ( editor ) {
    var dialog;
    return {
        title: 'Media Lookup',
        minWidth: 400,
        minHeight: 200,

        contents: [
            {
                id: 'planning-media-tab-basic',
                label: 'Basic Settings',
                elements: [
                    {
                        type: 'html',
                        html: '<p style="font-size:1.2em;margin-bottom:1em;">Use the widget below to find a media record that you would like to add.</p><div><input type="text" id="planning-media-id" /> \
                        <a class="related-lookup" id="lookup_planning-media-id" href="/admin/media/media/?_to_field=id" onclick="return showRelatedObjectLookupPopup(this);"></a></div>',

                        id: 'planning-media-master-id',
                        label: 'Media Master ID',
                        validate: CKEDITOR.dialog.validate.notEmpty( "Media field cannot be empty." ),
                        setup: function(element){
                            $("#planning-media-id").val( $(element.$).attr("data-content-id") ).trigger("change");
                        },
                        onLoad:function(element){
                            grp.jQuery("#planning-media-id").grp_autocomplete_fk({"autocomplete_lookup_url":"/grappelli/lookup/autocomplete/", "lookup_url":"/grappelli/lookup/related/"}); // init autocomplete using grapelli
                        },
                        commit: function(element){
                            var media_id = $("#planning-media-id").val();
                            $.ajax({
                                url:"/medialibrary/"+media_id+"/html/", 
                                success:function(data) {
                                    var new_element = CKEDITOR.dom.element.createFromHtml(data);
                                    if(dialog.preserved_classes){
                                        var classes = dialog.preserved_classes.split(" ");
                                        for (var i = 0; i < classes.length; i++) {
                                            new_element.addClass(classes[i]);
                                        }
                                    }
                                    
                                    dialog.element = new_element;
                                },
                                async:false,
                            });
                        },
                        onHide: function(element) {
                            $("#planning-media-id").val("");
                            $("#planning-media-id-autocomplete").val("");
                            $("#remove_planning-media-id").css("display","none");
                        }
                    }
                    // {
                    //  type: 'html', // the search widget for searching content
                    //  setup: function(html){

                    //  }
                    //  commit: function(html){ // setting the embeded media file

                    //  }
                    // },
                ]
            }
        ],
        onShow: function() {
            dialog = this;
            var selection = editor.getSelection();
            var element = selection.getStartElement();

            if ( element )
                element = element.getAscendant( function(el){
                    var has_plannningmedia_class = el && el.hasClass && el.hasClass("planning-media");
                    var is_img_or_link = el.getName ? ["img","a"].indexOf(el.getName()) > -1 : false;
                    return has_plannningmedia_class || is_img_or_link;
                }, true );

            if ( !element ) {
                element = editor.document.createElement( 'span' , {"attributes":{"class":"planning-media"}});
                this.insertMode = false;
            }else{
                this.insertMode = true;
            }

            if ( !element.hasClass('planning-media') ) {
                element.addClass('planning-media');
            }

            this.element = element;
            dialog.preserved_classes = element.getAttribute("class");

            this.setupContent( this.element );

        },
        onOk: function() {
            this.commitContent( this.element );
            // if (this.insertMode) {
            //     var selection = editor.getSelection();
            //     var selected_element = selection.getStartElement();
            //     var oldelement = selected_element.getAscendant( function(el){
            //         var has_plannningmedia_class = el && el.hasClass && el.hasClass("planning-media");
            //         var is_img_or_link = el.getName ? ["img","a"].indexOf(el.getName()) > -1 : false;
            //         return has_plannningmedia_class || is_img_or_link;
            //     }, true );
            //     oldelement.remove();
            // }
            editor.insertElement( this.element );
            dialog.preserved_classes = null;
        }
    };
});