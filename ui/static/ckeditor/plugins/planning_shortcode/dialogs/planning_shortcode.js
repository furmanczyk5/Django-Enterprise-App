var SHORTCODE_OPTIONS = [
    {
        "code":"BOOK_CAROUSEL",
        "title":"Book Carousel",
        "description":"Shows featured books",
        "params":[]
    },
    {
        "code":"SEARCH_BAR",
        "title":"Search Bar",
        "description":"Search Bar with no search results",
        "params": [
            {
                "verbose_name":"Search Url",
                "name":"search_url",
                "input_html": "<div><input name='search_url' type='text' placeholder='e.g. /cm/search/' /></div>"
                // IF TIME DO SOMETHING LIKE THIS
                // "<select name='search_url' class='cke_dialog_ui_input_select'> \
                //     <option value='/search/'>Global Search</option>\
                //     <option value=''>Other (specify below)</option>\
                //  </select>"
            }
        ]
    },
    {
        "code":"BLOG_LIST",
        "title":"Blog List",
        "description":"Displays a list of blog posts. Select the type records you want to show",
        "params": [
            {
                "verbose_name":"Tag ID",
                "name":"tag_id",
                "input_html": " <div>Enter a tag ID that you would like to filter results by</div>\
                                <div>Leave this blank if you are not filtering by tag</div>\
                                <div><input name='tag_id' type='text' /></div>"
            },
            {
                "verbose_name":"Template",
                "name":"template_name",
                "input_html": " <div>Select a template</div>\
                                <select name='template_name' class='cke_dialog_ui_input_select'>\
                                    <option value='ui/planning_shortcode/blogs.html'>Standard Website One Column</option>\
                                    <option value='ui/planning_shortcode/blogs-two-column.html'>Standard Website Two Column</option>\
                                    <option value='ui/planning_shortcode/blogs-conference.html'>Conference Microsite One Column</option>\
                                </select>"
            },
            {
                "verbose_name":"Max Results",
                "name":"max",
                "input_html": " <div>Enter the maximum number of results you would like to show</div>\
                                <div>Leave this blank if you don't want to limit the number of results</div>\
                                <div><input name='max' type='text' /></div>"
            }
        ]
    },
    {
        "code":"RESEARCH_RESOURCE_LIST",
        "title":"Research Resource List",
        "description":"Displays a list of records. Select the type records you want to show, the template you want to use",
        "params": [
            {
                "verbose_name":"Template",
                "name":"template_name",
                "input_html": " <div>Select a template</div>\
                                <select name='template_name' class='cke_dialog_ui_input_select'>\
                                    <option value='ui/planning_shortcode/resources-two-column.html'>Two Column, title and description</option>\
                                    <option value='ui/planning_shortcode/resources-two-column-w-place.html'>Two Column, title, place, and description</option>\
                                </select>"
            },
            {
                "verbose_name":"Collection Master ID",
                "name":"collection_id",
                "input_html": " <div>Enter a single Collection Master ID that you would like to filter results by</div>\
                                <div>Leave this blank if you are not filtering by collection</div>\
                                <div><input name='collection_id' type='text' /></div>"
            },
            {
                "verbose_name":"Tag ID",
                "name":"tag_id",
                "input_html": " <div>Enter a tag ID that you would like to filter results by</div>\
                                <div>Leave this blank if you are not filtering by tag</div>\
                                <div><input name='tag_id' type='text' /></div>"
            },
            {
                "verbose_name":"Master IDs",
                "name":"master_id_list",
                "input_html": " <div>Enter a list of comma-separated Master IDs for resources you would like to feature</div>\
                                <div>Leave this blank if you are not filtering by master IDs</div>\
                                <div><input name='master_id_list' type='text' /></div>"
            },
            {
                "verbose_name":"Knowledgebase",
                "name":"knowledgebase_type",
                "input_html": " <div>Select the type of Knowledgebase items you would like to include</div> \
                                <select name='knowledgebase_type' class='cke_dialog_ui_input_select'>\
                                    <option value='both' selected>All Knowledgebase records</option>\
                                    <option value='resources'>Resources only</option>\
                                    <option value='stories'>Stories only</option>\
                                </select>"
            },
            {
                "verbose_name":"Max Results",
                "name":"max",
                "input_html": " <div>Enter the maximum number of results you would like to show</div>\
                                <div>Leave this blank if you don't want to limit the number of results</div>\
                                <div><input name='max' type='text' /></div>"
            }
        ]
    },
    {
        "code":"RESEARCH_COLLECTION_LIST",
        "title":"Research Collection List",
        "description":"Displays a list of collections.",
        "params": [
            {
                "verbose_name":"Template",
                "name":"template_name",
                "input_html": " <div>Select a template</div>\
                                <select name='template_name' class='cke_dialog_ui_input_select'>\
                                    <option value='ui/planning_shortcode/resources-two-column.html'>Two Column, title and description</option>\
                                </select>"
            },
            {
                "verbose_name":"Tag ID",
                "name":"tag_id",
                "input_html": " <div>Enter a single tag ID that you would like to filter results by</div>\
                                <div>Leave this blank if you are not filtering by tag</div>\
                                <div><input name='tag_id' type='text' /></div>"
            },
            {
                "verbose_name":"Resources Master ID List",
                "name":"master_id_list",
                "input_html": " <div>Enter a list of comma-separated Master IDs for resources you would like to feature</div>\
                                <div>Leave this blank if you are not filtering by master IDs</div>\
                                <div><input name='master_id_list' type='text' /></div>"
            }
        ]
    },
    {
        "code":"FEATURED_CONTENT",
        "title":"Featured Content",
        "description":"Displays a single featured record",
        "params": [
            {
                "verbose_name":"Template",
                "name":"template_name",
                "input_html": " <div>Select a template</div>\
                                <select name='template_name' class='cke_dialog_ui_input_select'>\
                                    <option value='ui/planning_shortcode/featured-well-standard.html'>Well - Standard</option>\
                                    <option value='ui/planning_shortcode/featured-well-image.html'>Well - With Image</option>\
                                </select>"
            },
            {
                "verbose_name":"Content Master ID",
                "name":"master_id",
                "input_html": "<div>Enter the master ID of the record you would like to feature</div>\
                        <input name='master_id' type='text' maxlength='7' size='7' />"
            }
        ]
    },
    {
        "code":"DIRECTORY_ROSTER",
        "title":"Directory Roster",
        "description":"Displays a single featured record",
        "params": [
            {
                "verbose_name":"Directory Code",
                "name":"code",
                "input_html":  "<div>Enter the directory code for the list of contacts you want to display</div>\
                                <input name='code' type='text' />"
            }
        ]
    },
    {
        "code":"EVENTS_LIST",
        "title":"Event List",
        "description":"Displays a list of events/activities.",
        "params": [
            {
                "verbose_name":"Multipart Event Master ID",
                "name":"parent_id",
                "input_html": " <div>If you want to only show activities for a multipart event, enter the master id of that event. Otherwise leave this field blank</div>\
                                <div><input name='parent_id' type='text' /></div>"
            },
            {
                "verbose_name":"Tag IDs",
                "name":"tag_id",
                "input_html": " <div>If you want to filter events by tag, enter a comma-separated list of tag IDs that you would like to filter results by.</div>\
                                <div>Leave this blank if you are not filtering by tag</div>\
                                <div><input name='tag_id' type='text' /></div>"
            },
            {
                "verbose_name":"Resources Master ID List",
                "name":"master_id_list",
                "input_html": " <div>If you want to explicitly enter the list of events to show, enter a list of comma-separated Master IDs.</div>\
                                <div>Leave this blank if you are not filtering by master IDs</div>\
                                <div><input name='master_id_list' type='text' /></div>"
            }
        ]
    },
    {
        "code":"NEWS_LIST",
        "title":"News List",
        "description":"Displays a list of news stories.",
        "params": [
            {
                "verbose_name":"Category for API search",
                "name":"category",
                "input_html": " <div>Leave this blank if you are not filtering by category, otherwise enter given 'category' for search. Default is 'PLANNING combined'</div>\
                                <div><input name='category' type='text' /></div>"
            },
            {
                "verbose_name":"Number of Articles",
                "name":"articles",
                "input_html": " <div>Default is 3. If other number of responses is desired, Please enter here</div>\
                                <div>Leave this blank if you are not filtering by tag</div>\
                                <div><input name='articles' type='text' /></div>"
            },
        ]
    },
    {
        "code":"PLANNING_MAG_AD",
        "title":"Planning Magazine Ad",
        "description":"Displays an ad in a Planning Magazine article.",
        "params": [
            {
                "verbose_name":"Ad Slot",
                "name":"ad_slot",
                "input_html":  "<div>Enter the ad slot (1 or 2) you want to display</div>\
                                <input name='ad_slot' type='text' />"
            }
        ]
    },
]


CKEDITOR.dialog.add( 'planning_shortcode_Dialog', function ( editor ) {
    var dialog;
    return {
        title: 'Shortcode Lookup',
        minWidth: 400,
        minHeight: 200,

        contents: [
            {
                id: 'planning-shortcode-tab-basic',
                label: 'Basic Settings',
                elements: [
                    {
                        type: 'select',
                        id: 'planning-shortcode-select', // this does not set id attribute?
                        label: 'Select Shortcode',
                        items: SHORTCODE_OPTIONS.map(opt => [opt.title,opt.code]),
                        validate: CKEDITOR.dialog.validate.notEmpty( "Shortcode field cannot be empty." ),
                        setup: function(element){
                            dialog.shortcode_value = $(element.$).attr("data-planning-shortcode");
                            this.setValue( dialog.shortcode_value );
                            var input_element = this.getInputElement().$;
                            $(input_element).change(function(){
                                dialog.shortcode_value = $(input_element).val();
                                var shortcode_option = dialog.definition.getShortcodeOptionByCode(dialog.shortcode_value);
                                var params_html = dialog.definition.getInputFieldsFromOption(shortcode_option);
                                $("#planning-shortcode-dialog-params").html( params_html );
                                dialog.definition.setInputFieldValues();
                            });

                        },
                        // onLoad:function(element){
                        //     $("#planning-shortcode-select").val( $(element.$).attr("data-planning-shortcode") );
                        // },
                        commit: function(element){
                            //commit in onOK method
                        },
                        onHide: function(element) {
                            $(this.getInputElement().$).val("");
                        }
                    },

                    {
                        type: 'html',
                        html: '<div id="planning-shortcode-dialog-params"></div>',
                        id: 'planning-shortcode-params',
                        label: 'Shortcode Parameters',
                        setup: function(element){
                            // var shortcode_value = $(element.$).attr("data-planning-shortcode");
                            var shortcode_option = dialog.definition.getShortcodeOptionByCode(dialog.shortcode_value);
                            var params_html = shortcode_option ? dialog.definition.getInputFieldsFromOption(shortcode_option) : " - first select a shortcode - "
                            $("#planning-shortcode-dialog-params").html( params_html );
                            dialog.definition.setInputFieldValues();
                        },
                        // commit: function(element){

                        // },
                        onHide: function(element) {
                           $("#planning-shortcode-dialog-params").html("")
                        }
                    }
                ]
            }
        ],

        // CUSTOM METHODS
        setValuesFromElement: function(the_element){
            //pass in the [data-planning-shortcode] html element
            dialog.input_values = {};
            var children_parameters = the_element.getChildren().$;
            for (var i = 0; i < children_parameters.length; i++)  {
                var child_element = children_parameters[i];
                var param_name  = $("[data-planning-shortcode-param-name]", child_element).text();
                var param_value = $("[data-planning-shortcode-param-value]", child_element).text();
                if (param_name) {
                    dialog.input_values[param_name] = param_value;
                }
            }
        },
        getShortcodeOptionByCode: function(option_code) {
            var shortcode_option_list = SHORTCODE_OPTIONS.filter(function(the_opt){
                return the_opt.code == option_code;
            });

            if (shortcode_option_list) {
                return shortcode_option_list[0]
            } else {
                return null
            }
        },
        getInputFieldsFromOption: function(the_option) {
            //pass in the shortcode option that we want to set fields from
            var the_html = "";
            var the_params = the_option.params;
            for (var i = 0; i < the_params.length; i++){
                var param = the_params[i];
                var param_html = "<div style='padding:12px 0px;'><b>" + param.verbose_name + "</b>";
                param_html += param.input_html;
                param_html += "</div>";
                the_html += param_html;
            }
            return the_html || " - no parameters for selected shortcode - "
        },
        setInputFieldValues: function() {
            var shortcode_option = dialog.definition.getShortcodeOptionByCode(dialog.shortcode_value);
            var the_params = shortcode_option.params;
            for(var i = 0; i < the_params.length; i++){
                var param = the_params[i];
                var param_inputvalue = dialog.input_values[param.name];
                if (param_inputvalue) {
                    $("#planning-shortcode-dialog-params [name="+param.name+"]").val(param_inputvalue);
                }
            }
        },

        // DIALOG EVENT LISTENERS
        onShow: function() {
            dialog = this;
            var selection = editor.getSelection();
            var element = selection.getStartElement();

            if ( element ) {
                element = element.getAscendant( function(el){
                    return (el && el.getAttribute && el.getAttribute("data-planning-shortcode"));
                }, true);
            }

            if ( !element ) {
                element = editor.document.createElement( 'div' , {"attributes":{"data-planning-shortcode":""}});
                this.insertMode = false;
            }else{
                this.insertMode = true;
            }

            this.element = element;
            dialog.preserved_classes = element.getAttribute("class");

            // if ( this.insertMode ) {
            // }
            //set dialog values
            dialog.definition.setValuesFromElement(this.element);
            this.setupContent( this.element );
        },

        onOk: function() {
            var shortcode = dialog.getValueOf('planning-shortcode-tab-basic', 'planning-shortcode-select');
            var shortcode_option = dialog.definition.getShortcodeOptionByCode(shortcode);
            var shortcode_params = shortcode_option.params
            var the_html = "<div data-planning-shortcode='"+shortcode+"'>";
            the_html += "<span class='planning-shortcode-title'>"+shortcode_option.title+"</span>";
            the_html += "";
            for(var i = 0; i < shortcode_params.length; i++){
                var param = shortcode_params[i];
                var param_value = $("#planning-shortcode-dialog-params [name="+param.name+"]").val();
                the_html += "<span data-planning-shortcode-param>";
                the_html += "  <span data-planning-shortcode-param-name>"+param.name+"</span>";
                the_html += "  <span data-planning-shortcode-param-value>"+param_value+"</span>";
                the_html += "</span>";
            }
            the_html += "</div>";

            var new_element = CKEDITOR.dom.element.createFromHtml(the_html);
            this.element = new_element;

            this.commitContent( this.element );

            if (this.insertMode) {
                var selection = editor.getSelection();
                var selected_element = selection.getStartElement();
                var oldelement = selected_element.getAscendant( function(el){
                    return (el && el.getAttribute && el.getAttribute("data-planning-shortcode"));
                }, true);
                oldelement.remove();
            }
            editor.insertElement( this.element );
            dialog.preserved_classes = null;
        }
    };
});
