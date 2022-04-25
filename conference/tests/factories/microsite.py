
import factory

from conference.models.microsite import Microsite


class MicrositeFactory(factory.DjangoModelFactory):

    event_master = None  # factory.subfactory content.MasterContent
    home_page = None  # factory.subfactory LandingPageMasterContent
    search_filters = None  # factory.subfactory content.TagType
    program_search_filters = None
    is_npc = True
    short_title = None
    url_path_stem = "conference"
    home_page_code = "CONFERENCE_HOME"
    show_skip_to_dates = True
    status = 'A'
    deactivation_date = None
    header_ad = None
    sidebar_ad = None
    footer_ad = None
    custom_color = None
    hero_image_path = "newtheme/image/conference-hero-bg.jpg"
    home_summary_blurb = None
    signpost_logo_image_path = "newtheme/image/npc-sign.png"
    program_blurb = None
    nosidebar_breakout_image_path = "newtheme/image/content-header-conference-image-breakout-default.jpg"
    text_blurb_one = None
    # details_inclusive_blurb = None
    details_local_blurb = None

    class Meta:
        model = Microsite
