var newtheme = newtheme || {};

//namespace just in case
(function( o ){

    o.initializeMyAPABookmarks = function () {
        var self = this;

        //Instead of loading AddThis' javascript on every single page, we will only lazy-load it if we detect that it is needed.
        var $bookmarkElements = jQuery('.myapa-bookmark-widget');

        $bookmarkElements.each(function () {
            //////////////
            // Properties
            //////////////
            var content_id,
                is_bookmarked,
                is_busy,
                all_bookmarks_state;

            //////////////
            // Elements
            //////////////
            var $widget = $(this),
                $element_toggle,
                $element_toggle_text,
                $element_toggle_icon,
                $element_all_bookmarks;


            //////////////
            // Methods
            //////////////
            function init () {
                is_busy = false;

                /* Load data from widget: */
                content_id = $widget.data('content-id');
                is_bookmarked = ($widget.data('is-bookmarked') === 1);
                all_bookmarks_state = $widget.data('all-bookmarks');

                if (!content_id) {
                    alert('No content ID!!!!');
                    return;
                }

                /* Inject HTML into widget */
                /*
                <div class="myapa-bookmark-widget">
                    <button class="myapa-bookmark-widget-toggle ?is-busy ?is-bookmarked">
                        <span class="text">...</span>
                        <span class="icon"></span>
                    </button>
                </div>
                 */
                $element_toggle = $('<button />', {
                    'type': 'button',
                    'class': 'myapa-bookmark-widget-toggle'
                });

                $element_toggle_text = $('<span />', {
                    'class': 'myapa-bookmark-widget-toggle-text'
                });

                $element_toggle_icon = $('<span />', {
                    'class': 'myapa-bookmark-widget-toggle-icon'
                });

                $element_all_bookmarks = $('<a />', {
                    'href': '/myapa/bookmarks',
                    'class': 'myapa-bookmark-widget-see-all',
                    'text': 'My Bookmarks'
                });

                $element_toggle.append($element_toggle_text);
                $element_toggle.append($element_toggle_icon);

                $widget.append($element_toggle);

                if (all_bookmarks_state != 'hide') {
                    $widget.append($element_all_bookmarks);
                }

                /* Wire up actions for clicking on the toggle element */
                $element_toggle.on('click', function () {
                    var promise;

                    if (is_busy) {
                        //If is busy, don't allow any input
                        return;
                    }

                    if (is_bookmarked) {
                        //Is already bookmarked, so remove bookmark
                        promise = self.deleteBookmarkForContent(content_id);
                        is_busy = true;
                        refresh_view();


                        promise.done(function () {
                            is_bookmarked = false;
                            is_busy = false;
                            refresh_view();
                        });

                        promise.fail(function () {
                            alert('We\'re sorry, something went wrong while adding your bookmark.Please try again later.');
                            is_busy = false;
                            refresh_view();
                        });
                    }
                    else
                    {
                        //Is not bookmarked, so add bookmark
                        promise = self.createBookmarkForContent(content_id);
                        is_busy = true;
                        refresh_view();

                        promise.done(function () {
                            is_bookmarked = true;
                            is_busy = false;
                            refresh_view();
                        });

                        promise.fail(function () {
                            alert('We\'re sorry, something went wrong with your bookmark. Please try again later.');

                            is_busy = false;
                            refresh_view();
                        });
                    }
                });

                /* Refresh view once after initialization */
                refresh_view();
            }

            function refresh_view () {
                if(is_busy) {
                    $widget.addClass('is-busy');
                    $element_toggle_text.text('Saving...');
                }
                else
                {
                    $widget.removeClass('is-busy');
                    if(is_bookmarked) {
                        $widget.addClass('is-bookmarked');
                        $element_toggle_text.text('Remove Bookmark');
                    }
                    else
                    {
                        $widget.removeClass('is-bookmarked');
                        $element_toggle_text.text('Bookmark This Page ');
                    }
                }
            }

            ///////////////////
            /// Initialize
            //////////////////
            init();

        });
    }

    /**
     * Create a bookmark for a piece of content. Returns a jQuery deferred promise for async handling.
     * @param content_id
     */
    o.createBookmarkForContent = function (content_id) {
        if (!content_id) {
            console.warn('Tried running createBookmarkForContent with no content_id!');
            return;
        }

        var deferred = jQuery.Deferred(); //jQuery promises

        jQuery
            .ajax({
                method: 'GET',
                url: '/myapa/bookmark/' + content_id + '/',
                data: {
                    'action': 'create'
                },
                cache: false,
                dataType: 'json'
            })
            .done(function(data) {

                if(data.success === true) {
                    deferred.resolve();
                }
                else
                {
                    deferred.reject();
                }
            })
            .fail(function () {
                deferred.reject();
            });

        return deferred.promise();
    }

    /**
     * Delete a bookmark for a piece of content. Returns a jQuery deferred promise for async handling.
     * @param content_id The content ID of the content to delete the bookmark
     */
    o.deleteBookmarkForContent = function (content_id) {
        if (!content_id) {
            console.warn('Tried running deleteBookmarkForContent with no content_id!');
            return;
        }

        var deferred = jQuery.Deferred(); //jQuery promises

        jQuery
            .ajax({
                method: 'GET',
                url: '/myapa/bookmark/' + content_id + '/',
                data: {
                    'action': 'delete'
                },
                cache: false,
                dataType: 'json'
            })
            .done(function(data) {

                if(data.success === true) {
                    deferred.resolve();
                }
                else
                {
                    deferred.reject();
                }
            })
            .fail(function () {
                deferred.reject();
            });

        return deferred.promise();
    }

})(newtheme);

$(function() {
  newtheme.initializeMyAPABookmarks();
});
