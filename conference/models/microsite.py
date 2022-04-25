from django.db import models

from content.models import MenuItem
from events.models import Activity


class Microsite(models.Model):
    # ********************
    # *** Foreign Keys ***
    # ********************

    @classmethod
    def get_microsite(cls, url):
        # if starts with /conference/*/ then we know it's a microsite, therefor query Microsite model
        # call select_related for event_master and event_master.content_live

        tokens = url.split("/")
        if len(tokens) > 0:
            first_url_dir = tokens[1]
        else:
            first_url_dir = None

        if first_url_dir == "conference" or first_url_dir == "registrations":
            if len(tokens) > 2 and tokens[2] != '':
                url_path_stem = tokens[2]
                ms = Microsite.objects.filter(url_path_stem=url_path_stem).first()
                if not ms:
                    ms = Microsite.objects.filter(is_npc=True, status="A").first()
                return ms
            else:
                return Microsite.objects.filter( is_npc=True, status="A" ).first()
        elif first_url_dir == "events":
            # Since we've changed event links in the results-list-item.html template
            # to point to /events/activity
            # instead of /conference/nationalconferenceactivity,
            # we need to ensure we're still getting the Microsite associated with
            # the event so that :obj:`content.views.render_content.RenderContent`
            # has the Microsite context
            if len(tokens) >= 3 and tokens[2] == "activity":
                activity = Activity.objects.filter(
                    master_id=tokens[3],
                    publish_status="PUBLISHED"
                )
                if activity.exists():
                    microsite = activity.first().parent.event_microsite
                    if microsite.exists():
                        return microsite.first()
        return None

    def get_program_search_filter_codes(self):
        return [psf.code for psf in self.program_search_filters.all()]

    event_master = models.ForeignKey(
        'content.MasterContent',
        related_name="event_microsite",
        blank=True,
        null=True,
        help_text="Event associated with microsite",
        on_delete=models.SET_NULL
    )

    home_page = models.ForeignKey(
        "pages.LandingPageMasterContent",
        verbose_name="Microsite home page",
        related_name="home_page_microsite",
        blank=True,
        null=True,
        help_text="""The page that holds the top bar mega menu nav""",
        on_delete=models.SET_NULL
    )

    # TO BE DELETED:
    search_filters = models.ForeignKey(
        "content.TagType",
        verbose_name="Microsite search filters",
        related_name="microsite",
        blank=True, null=True,
        help_text="""The search filters for the microsite""",
        on_delete=models.SET_NULL
    )

    program_search_filters = models.ManyToManyField(
        "content.TagType",
        verbose_name="Microsite search filters",
        related_name="micro_site",
        blank=True,
        help_text="""The search filters for the microsite"""
    )

    # ********************
    # *** ID INFO ********
    # ********************
    is_npc = models.BooleanField("Is NPC", default=False)
    short_title = models.CharField("Short title", max_length=50, blank=True, null=True)
    url_path_stem = models.CharField("Microsite identifier", max_length=50, default="conference")
    home_page_code = models.CharField("Microsite home page code", max_length=50, default="CONFERENCE_HOME")
    # cache_file = models.CharField(max_length=50, default="conferencemenu-query.p")

    # ********************
    # *** SETTINGS *******
    # ********************
    show_skip_to_dates = models.BooleanField("Show skip to dates", default=True)
    status = models.CharField("microsite status", max_length=5, default='A')
    deactivation_date = models.DateTimeField("Deactivation date", blank=True, null=True)

    # ********************
    # *** ADS ************
    # ********************
    # these must be file paths -- the files should be in:
    # template_app/templates/newtheme/sandbox/banner-ad/  ?? sandbox ??
    # so example value of header_ad would be:
    # "newtheme/sandbox/banner-ad/policy-header-ad.html"
    header_ad = models.TextField("Microsite header ad html", blank=True, null=True)
    sidebar_ad = models.TextField("Microsite sidebar ad html", blank=True, null=True)
    footer_ad = models.TextField("Microsite footer ad html", blank=True, null=True)
    interstitial_ad = models.TextField("Microsite interstitial ad html", blank=True, null=True)

    internal_header_ad = models.TextField("Microsite internal header ad html", blank=True, null=True)
    internal_sidebar_ad = models.TextField("Microsite internal sidebar ad html", blank=True, null=True)
    internal_footer_ad = models.TextField("Microsite internal footer ad html", blank=True, null=True)
    internal_interstitial_ad = models.TextField("Microsite internal interstitial ad html", blank=True, null=True)

    # ********************
    # *** CUSTOMISATION **
    # ********************
    custom_color = models.CharField(max_length=50, blank=True, null=True,
        help_text="hex value of conference microsite custom color")
    # home page customisation
    hero_image_path = models.CharField(max_length=100, default="newtheme/image/conference-hero-bg.jpg")
    home_summary_blurb = models.TextField("Microsite summary html blurb", blank=True, null=True)
    signpost_logo_image_path = models.CharField(max_length=100, default="newtheme/image/npc-sign.png")
    program_blurb = models.TextField("Program html blurb", blank=True, null=True)
    # program pages customisation
    nosidebar_breakout_image_path = models.CharField(max_length=100, default="newtheme/image/content-header-conference-image-breakout-default.jpg")
    # details page customisation
    # details_inclusive_blurb = models.TextField("Inclusiveness/Social Justice html blurb", blank=True, null=True)
    details_local_blurb = models.TextField("Local/Regional html blurb", blank=True, null=True)
    interactive_educational_session = models.TextField("Interactive Educational Session html blurb", blank=True, null=True)
    text_blurb_one = models.TextField("All purpose text blurb number one", blank=True, null=True)

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    @staticmethod
    def construct_url(*args):
        """
        Construct a valid URL from the input str args by separating them with a slash (/)
        Slashes passed in to any element of args will be silently discarded

        >>> construct_url('search', 'pdf-inline')
        '/search/pdf-inline'

        >>> construct_url('conference', 'water', 'program', 'search')
        '/conference/water/program/search'

        >>> construct_url('conference/', '/policy', '/search/')
        '/conference/policy/search'

        :param args: str, URI components to separate with a /
        :return: str
        """
        # strip components of all slashes
        components = [x.replace('/', '').strip() for x in args]
        # strip empty string components
        components = [x for x in components if x.strip()]
        # construct the endpoint
        endpoint = '/'
        endpoint += '/'.join(components)
        return endpoint

    def get_endpoint(self, *args):
        """
        Construct a valid endpoint for a Microsite. NPC is just /conference; other
        non-NPC microsites will be /conference/{self.url_path_stem}

        :param args: str, URL components to separate with a /
        :return: str
        """
        if self.is_npc:
            return Microsite.construct_url('conference', *args)
        return Microsite.construct_url('conference', self.url_path_stem, *args)

    @property
    def search_url(self):
        """
        The search URL to use for the Microsite, typically in <a> tags in HTML templates

        :return: str
        """
        return self.get_endpoint('search')

    @property
    def program_search_url(self):
        """
        The program session activities URL to use for the Microsite
        :return: str
        """
        return self.get_endpoint('program', 'search') + '/'

    @property
    def pdf_inline_url(self):
        """
        Generate a link to the PDF exports of conference schedules. To be used in
        conference/templates/conference/newtheme/program/search.html

        :return: str
        """
        return self.get_endpoint('search', 'pdf-inline')

    @property
    def schedule_url(self):
        """
        Generate a link to the conference schedule builder

        :return: str
        """
        return self.get_endpoint('schedule')

    @property
    def glossary_url(self):
        """
        Generate a link to the conference schedule builder

        :return: str
        """
        return self.get_endpoint('program#glossary')

    @property
    def has_schedule_menuitem(self):
        """
        Whether or not the Landing Page for this Microsite has a MenuItem that links to
        "/conference/schedule". This will be passed in to the template context and used
        to control whether or not to display the "Add to My Schedule/Add to Cart" buttons.
        `JIRA Ticket DEV-4829 <https://americanplanning.atlassian.net/browse/DEV-4829>`_

        :return: bool
        """
        root_menu = MenuItem.get_root_menu(landing_code=self.home_page_code)
        # URLs (including one with a trailing slash just in case...) to test
        # for links to My Schedule
        if self.is_npc:
            schedule_urls = ("/conference/schedule", "/conference/schedule/")
        else:
            schedule_urls = ("/conference/{}/schedule".format(self.url_path_stem),
                             "/conference/{}/schedule/".format(self.url_path_stem))
        # First check the top level MenuItems
        if root_menu.filter(url__in=schedule_urls).exists():
            return True
        # If necessary, loop through the root MenuItems and test if any of their children
        # are pointing to /schedule
        # TODO: make this a recursive function if we use nested menus with children of children
        # with children of children of children hahahaha recursion humor
        for menu in root_menu:
            children = menu.get_child_menuitems()
            if isinstance(children, models.QuerySet):
                if children.filter(url__in=schedule_urls).exists():
                    return True
        return False

    def __str__(self):
        return "%s Microsite" % (self.short_title if self.short_title else "<Untitled>")
