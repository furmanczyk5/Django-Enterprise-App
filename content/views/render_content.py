from functools import reduce
from urllib.parse import urlencode

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView
from sentry_sdk import capture_exception

from conference.models import Microsite
from conference.models.microsite_attendee import Attendee
from conference.models.settings import JOIN_WAITLIST_URL
from content.models import Content, MessageText, MenuItem, Tag, TagType, ContentTagType, ContentRelationship
from content.utils import content_class_from_content
from imis.event_tickets import is_waitlist_in_imis, is_ordered_in_imis
from imis.models import CustomEventSchedule, Name
from learn.utils.wcw_api_utils import WCWContactSync
from myapa.models.proxies import Bookmark
from store.models import Purchase, ProductCart, ProductOption, Product
from store.utils.scholarlab import ScholarLab

MEMBER_LOGIN_GROUPS = ("member", "planning")
PAN_LOGIN_GROUPS = ("PAN",)
AICP_LOGIN_GROUPS = ("aicpmember",)
SUBSCRIBER_LOGIN_GROUPS = ("PAS", "ZONING", "JAPA")

# TODO: New NPC groups should always be added to the end of this,
# myapa.views.account.MyapaOverviewView.get_membership_info relies on this pattern
REGISTRATION_LOGIN_GROUPS = ("16CONF", "17CONF", "18CONF", "19CONF", "NPC20-digital", "NPC21")

DIVISION_LOGIN_GROUPS = ("CITY_PLAN", "LAP", "SMALL_TOWN", "TRANS",
                         "URBAN_DES", "WOMEN", "LAW", "NEW_URB", "PLAN_BLACK",
                         "PRIVATE", "SCD", "CPD", "ECON", "FED_PLAN", "GALIP",
                         "HMDR", "HOUSING", "INFO_TECH", "INTER_GOV", "INTL",
                         "ENVIRON")
CHAPTER_LOGIN_GROUPS = ("chapter", "CHAPT_AK", "CHAPT_KS", "CHAPT_MD",
                        "CHAPT_NV", "CHAPT_VA")


class RenderContent(TemplateView):
    product = None
    conf_menu_query = None
    microsite = None
    contact = None

    def get(self, request, *args, **kwargs):
        self.get_user_authentication()
        self.set_content(request, *args, **kwargs)
        self.set_contenttagtypes(request, *args, **kwargs)
        self.set_microsite(request, *args, **kwargs)
        permissions_response = self.check_permissions()
        if permissions_response:
            return permissions_response
        else:
            if hasattr(self.content, "product"):
                self.set_product_cart()
                # FIXME: This doesn't handle anonymous users
                self.set_purchase()
            if getattr(self.content, 'content_type') == 'PUBLICATION':
                self.set_contributors()
            return super().get(request, *args, **kwargs)

    def get_user_authentication(self, *args, **kwargs):
        self.user_is_loggedin = self.request.user.is_authenticated()
        self.user_groups = set(self.request.user.groups.all())
        self.user_is_staff = (
            self.request.user.is_staff or
            "staff" in (g.name for g in self.user_groups))
        if self.user_is_loggedin:
            self.user = self.request.user
            self.contact = self.user.contact

    def check_permissions(self, *args, **kwargs):
        required_groups = set(self.content.permission_groups.all())
        required_group_names = set([group.name for group in required_groups])

        has_permission = (
            (not required_groups) or
            (required_groups & self.user_groups) or
            (self.user_is_staff))

        if not has_permission and not self.content.show_content_without_groups:

            if not self.user_is_loggedin:
                msg = MessageText.objects.filter(code="LOGIN_REDIRECT").first()
                messages.warning(self.request, msg.text)
                return redirect('/login/?next=%s' % self.request.path)

            if required_group_names & set(MEMBER_LOGIN_GROUPS):
                msg_code = "NOT_APA_MEMBER"
            elif required_group_names & set(AICP_LOGIN_GROUPS):
                msg_code = "NOT_AICP_MEMBER"
            elif required_group_names & set(SUBSCRIBER_LOGIN_GROUPS):
                msg_code = "NOT_SUBSCRIBER"
            elif required_group_names & set(REGISTRATION_LOGIN_GROUPS):
                msg_code = "NOT_REGISTERED"
            elif required_group_names & set(DIVISION_LOGIN_GROUPS):
                msg_code = "NOT_DIVISION_MEMBER"
            elif required_group_names & set(CHAPTER_LOGIN_GROUPS):
                msg_code = "NOT_CHAPTER_MEMBER"
            elif required_group_names & set(PAN_LOGIN_GROUPS):
                msg_code = "NOT_PAN_MEMBER"
            else:
                msg_code = "AUTO_LOGIN_DENIAL"

            msg = MessageText.objects.get(code=msg_code)

            self.permission_error_message = msg

        self.required_groups = required_groups
        self.has_permission = has_permission

        return None

    def set_content(self, request, *args, **kwargs):

        path = request.path.replace("/mobile/", "/", 1).lower()
        # STAFF ARE ALLOWED TO PREVIEW NON-PUBLISHED VERSIONS
        publish_status = request.GET.get("publish_status", "PUBLISHED") if self.user_is_staff else "PUBLISHED"
        # SMALL INITIAL QUERY ...
        #  TO DETERMINE CONTENT TYPE OF RECORDS WITH CUSTOM URLS
        prequery_content = Content.objects.filter(
            status__in=("A", "H"),
            publish_status=publish_status,
            url=path
        ).only(
            "content_type", "landingpage"
        ).order_by("published_time").last()

        if prequery_content:
            # THEN QUERY BY CUSTOM URL
            content_class = content_class_from_content(prequery_content)
            self.content = content_class.objects.with_details().filter(
                status__in=("A", "H"),
                publish_status=publish_status,
                url=path
            ).order_by("published_time").last()
        else:
            # THEN TRY QUERY BY URL PATTERN
            try:
                path_parts = path.strip("/").split("/")
                app = path_parts[0]
                model = path_parts[1]
                # TO DO... These hard-coded exceptions are a little screwy...
                if model in ("publicationdocument","learncourse"):
                    raise Http404("Content record not found.")
                if app == "publications" and model == "document":
                    model = "publicationdocument"
                elif app == "learn" and model == "course":
                    model = "learncourse"
                elif app == "learn" and model == "bundle":
                    model = "learncoursebundle"
                record_identifier = path_parts[2]  # could be slug or master_id
                ModelClass = apps.get_model(app_label=app, model_name=model)
                self.content = ModelClass.objects.with_details().filter(
                    status__in=("A", "H"),
                    publish_status=publish_status,
                    master_id=record_identifier
                ).order_by("published_time").last()

                if app == "learn":
                    try:
                        self.pull_learn_completions(request, *args, **kwargs)
                    except:
                        # TO DO: report to Sentry
                        pass

            except:
                self.content = None

        if not self.content:
            raise Http404("Content record not found.")

        if self.content:
            self.app = self.content._meta.app_label
            self.model = self.content._meta.model_name
            self.parent_landing = self.content.get_parent_landing_page()
            self.ancestors = self.content.get_landing_ancestors()

        return self.content

    def set_contenttagtypes(self, request, *args, **kwargs):
        if self.content and self.content.active_contenttagtypes:
            # TODO: is this hitting the db on every iteration?
            # :meth:`content.models.content.ContentManager.with_details`
            for ctt in self.content.active_contenttagtypes:
                try:
                    setattr(self.content, "contenttagtype_" + ctt.tag_type.code, ctt)
                except:
                    pass

    def set_product_cart(self):
        try:
            self.product = ProductCart.objects.get(content=self.content)
            #part of ProductCart bug where not returning productCart
            if self.product is None:
                self.product = Product.objects.get(content=self.content)

            if self.product.options:
                for option in self.product.options.all():
                    setattr(option, "my_price", self.product.get_price(contact=self.contact, option=option))
            if self.user_is_loggedin:
                self.product_prices = self.product.get_prices(contact=self.contact)
                self.my_price = next( (price for price in self.product_prices if price.applies), None)
            self.set_contributors()
        except ProductCart.DoesNotExist:
            pass
        except Exception as exc:
            capture_exception(exc)

    def set_purchase(self):
        if self.content.product.product_type in (
            'DIGITAL_PUBLICATION',
            'PUBLICATION_SUBSCRIPTION',
            'EBOOK',  # TO DO: consider removing,
            'STREAMING',
            'LEARN_COURSE'
        ):

            user = None
            if self.user_is_loggedin:
                user = self.request.user

            self.purchase = Purchase.objects.filter(
                product__content__master=self.content.master,
                user=user
            ).exclude(
                order__isnull=True
            ).order_by(
                "-expiration_time"
            ).first()

            # gives user access to to resources based on permission groups
            if self.content.show_content_without_groups and not self.purchase:
                self.purchase = bool(self.has_permission)

            # streaming product - !!SHOULDNT HARD CODE THIS HERE
            if self.content.product.code == "STR_EXAM3":
                self.str_exam3_url = ScholarLab().authorize(self.request.user)


    def set_contributors(self):
        self.authors = [cr for cr in self.content.contactrole.all() if cr.role_type == "AUTHOR"]
        self.publishers = [cr for cr in self.content.contactrole.all() if cr.role_type == "PUBLISHER"]
        self.speakers = [cr for cr in self.content.contactrole.all() if cr.role_type == "SPEAKER"]

        if self.content.content_type == 'PUBLICATION' and self.content.content_area == 'KNOWLEDGE_CENTER' \
            and self.content.resource_type == 'ARTICLE':
            name_list = []
            for cr in self.authors:
                if cr.first_name and cr.last_name:
                    full_name = " ".join(n for n in [cr.first_name, cr.middle_name, cr.last_name] if n)
                    if full_name:
                        name_list.append(full_name)
                elif cr.contact:
                    im = Name.objects.filter(id=cr.contact.user.username).first()
                    if im:
                        full_name = getattr(im, 'full_name', '') or " ".join(n for n in [im.first_name, im.middle_name, im.last_name] if n)
                        if full_name:
                            name_list.append(full_name)
                    else:
                        full_name = " ".join(n for n in [cr.contact.first_name, cr.contact.middle_name, cr.contact.last_name] if n)
                        if full_name:
                            name_list.append(full_name)

            self.planning_mag_authors = "; ".join(name_list)
        else:
            self.planning_mag_authors = ""


    def get_template_names(self):
        return [self.content.template]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["is_authenticated"] = self.user_is_loggedin
        context["contact"] = self.contact
        if self.user_is_loggedin:
            context["user"] = self.contact.user
            if self.content.content_type == "PAGE_JOTFORM":
                context.update(self.get_jotform_context())
        context["is_staff"] = self.user_is_staff
        context["access_denied"] = not self.has_permission and not self.content.show_content_without_groups
        context["required_groups"] = self.required_groups
        context["access_denied_message"] = getattr(self, "permission_error_message", None)

        context["content"] = self.content
        context["title"] = self.content.title
        context["subtitle"] = self.content.subtitle
        context["parent_landing"] = self.parent_landing
        context["ancestors"] = self.ancestors
        context["bookmarked"] = self.user_is_loggedin and Bookmark.objects.filter(contact=self.request.user.contact, content=self.content).exists()

        context["resource_url"] = self.content.resource_url
        context["resource"] = self.content.resource_url

        context["product"] = getattr(self, "product", None)
        context["product_prices"] = getattr(self, "product_prices", None)
        context["my_price"] = getattr(self, "my_price", None)
        context["purchase"] = getattr(self, "purchase", None)
        context["str_exam3_url"] = getattr(self, "str_exam3_url", None)
        context["authors"] = getattr(self, "authors", None)
        context["publishers"] = getattr(self, "publishers", None)
        context["speakers"] = getattr(self, "speakers", None)
        context["product_details_list"] = ["BOOK", "EBOOK", "DIGITAL_PUBLICATION"] # TO DO... consider removing
        context["conference_menu"] = self.conf_menu_query
        context["microsite"] = self.microsite
        context["search_url"] = self.search_url
        context["LEARN_DOMAIN"] = settings.LEARN_DOMAIN
        context["LEARN_DOMAIN_CATALOG"] = "https://{}/catalog/".format(context["LEARN_DOMAIN"])
        # add the event attendee to the template context in the case of conference activities
        # so that they can log CM credits if appropriate

        if self.user_is_loggedin and self.is_event():
            context['is_registered'] = self.is_registered()
            context['has_ticket'] = self.has_ticket(context)
            context['is_waitlist'] = self.is_waitlist()
            context['is_ordered'] = self.is_ordered()

        context.update(self.content.details_context())

        try:
            edit_url_name = "admin:{app}_{model}_change".format(
                app=self.app, model=self.model)
            context["edit_link"] = reverse(
                edit_url_name,
                args=[self.content.master.content_draft.id])
        except:
            context["edit_link"] = '/admin/'

        tag_types = self.content.contenttagtype.all()

        contenttagtype_transit = tag_types.filter(
            tag_type__code="TRANSIT").first()
        contenttagtype_room = tag_types.filter(
            tag_type__code="ROOM").first()
        contenttagtype_type = tag_types.filter(
            tag_type__code="EVENTS_NATIONAL_TYPE").first()

        if contenttagtype_type:
            context["activity_type"] = contenttagtype_type.tags.first()

        # TODO: This is overwriting the existing value of product set above
        # This method seems to usually return Product, not ProductCart, which
        # causes all sorts of issues
        # context["product"] = self.content.get_product()

        if self.content.content_type == "EVENT":
            context["is_apa_learn_product"] = (
                    getattr(self.content, "digital_product_url", None) is not None and
                    getattr(self.content, "digital_product_url", None) != 'https://learn.planning.org/catalog/' and
                    (
                        settings.LEARN_DOMAIN in self.content.digital_product_url
                        or "learn.planning.org" in self.content.digital_product_url
                    ))

        if self.request.user.is_authenticated():
            context["attendee"] = Attendee.objects.filter(
                contact=self.request.contact,
                event__master=self.content.master).first()
            # this is the attendee record for the individual activity
            # (for adding/removing to schedule)
            context["event_attendee"] = Attendee.objects.filter(
                contact=self.request.contact,
                event__master=self.content.parent).first()
            # this is the attendee record for the overall event

        if self.content.content_type == "EVENT":
            context["has_downloads"] = ((self.content.resource_url and
                                         context.get("event_attendee", None)) or
                                        getattr(self.content, "digital_product_url", None))

        if contenttagtype_transit:
            context["mobile_workshop_codes"] = [
                t.code
                for t in contenttagtype_transit.tags.all()
            ]

        if contenttagtype_room:
            context["room"] = next(
                (t.title for t in contenttagtype_room.tags.all()),
                None)

        local_tag = Tag.objects.get(code="LOCAL")
        # inclusiveness_tag = Tag.objects.get(code="INCLUSIVENESS")
        interactive_tag = Tag.objects.get(code="INTERACTIVE")
        recorded_tag = Tag.objects.get(code="RECORDED_SESSION")
        context["is_local"] = False
        # context["is_inclusive"] = False
        context["is_interactive"] = False
        context["is_recorded"] = False
        npc_category_tag_type = TagType.objects.get(code='NPC_CATEGORY')
        npc_ctt = ContentTagType.objects.filter(
            tag_type=npc_category_tag_type,
            content=self.content).first()
        if npc_ctt:
            npc_cat_tags = npc_ctt.tags.all()
            if local_tag in npc_cat_tags:
                context["is_local"] = True
            # if inclusiveness_tag in npc_cat_tags:
            #     context["is_inclusive"] = True
            if interactive_tag in npc_cat_tags:
                context["is_interactive"] = True
            if recorded_tag in npc_cat_tags:
                context["is_recorded"] = True

        context["join_waitlist_url"] = JOIN_WAITLIST_URL
        # FLAGGED FOR REFACTORING: NPC21
        context["show_schedule_stuff"] = False

        if self.content.content_type == 'PUBLICATION' and self.content.content_area == 'KNOWLEDGE_CENTER' \
            and self.content.resource_type == 'ARTICLE':
            context["planning_mag_sections"] = self.get_planning_mag_tags("PLANNING_MAG_SECTION")
            context["planning_mag_slugs"] = self.get_planning_mag_tags("PLANNING_MAG_SLUG")
            context["planning_mag_series"] = self.get_planning_mag_tags("PLANNING_MAG_SERIES")
            context["planning_mag_recommended"] = self.get_planning_mag_recommended()

        context["planning_mag_authors"] = getattr(self, "planning_mag_authors", None)

        return context

    def set_microsite(self, request, *args, **kwargs):
        microsite = Microsite.get_microsite(self.request.get_full_path())

        if not microsite and self.content:
            microsite = self.content.master.event_microsite.first()
            if not microsite and self.content.parent:
                microsite = self.content.parent.event_microsite.first()

        self.search_url = "/search/"
        if microsite:
            # means we are in a conf microsite (not incl npc)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=microsite.home_page_code)
            self.microsite = microsite
            self.search_url = microsite.search_url
        elif self.content.template[:12]=="pages/micro/":
            landing_code = next( (lp.code for lp in self.ancestors[::-1] if lp.code), None)
            self.conf_menu_query = MenuItem.get_root_menu(landing_code=landing_code)
        else:
            self.conf_menu_query = None

    def pull_learn_completions(self, request, *args, **kwargs):
        contact = getattr(request.user, "contact", None)
        if contact:
            wcw_contact_sync = WCWContactSync(request.user.contact)
            wcw_contact_sync.pull_course_completions_from_wcw()

    def is_event(self):
        return hasattr(self.content, 'event_type')

    def has_ticket(self, context, code=None):
        if getattr(self, "product", None):
            code = self.product.imis_code
        else:
            code = self.content.code

        return self.ticket_exists_in_imis(code)

    def is_registered(self):
        # TO DO: REMOVE THIS TRY EXCEPT ... DONE:removed Bare except
        try:
            if hasattr(self.content, 'parent'):
                parent = self.content.parent
                if parent is None:
                    return False
                event = self.content.parent.content_live.event
                meeting = event.product.imis_code
                product_options = ProductOption.objects.filter(
                    product=event.product).exclude(code='M004')  # To exclude Badge Only registrants

                query = reduce(
                    lambda x, y: x | y,
                    [Q(product_code=meeting +'/' + option.code)
                        for option in product_options])
                query.add(Q(id=self.request.user.username), Q.AND)
                query.add(Q(status='A'), Q.AND)

                return bool(CustomEventSchedule.objects.filter(query))
        except Exception as e:
            capture_exception(e)
            return False

    def ticket_exists_in_imis(self, code):
        return bool(CustomEventSchedule.objects.filter(
                id=self.request.user.username,
                product_code=code,
                status='A'
            ))

    def is_waitlist(self):
        if getattr(self, "product", None):
            code = self.product.imis_code
        else:
            code = self.content.code
        username = self.request.user.username
        return is_waitlist_in_imis(None, username=username, product_code=code)

    def is_ordered(self):
        if getattr(self, "product", None):
            code = self.product.imis_code
        else:
            code = self.content.code
        username = self.request.user.username
        return is_ordered_in_imis(None, username=username, product_code=code)

    def get_jotform_context(self):
        context = {}

        imis_std_contact_fields = self.contact.get_standard_fields()
        embed_url = '{0}?{1}'.format(self.content.resource_url, urlencode(imis_std_contact_fields))

        context["std_contact_info"] = imis_std_contact_fields
        context["jotform_embed_url"] = embed_url

        return context

    def get_planning_mag_tags(self, tag_type_code):

        tt = TagType.objects.filter(code=tag_type_code).first()

        ctt = ContentTagType.objects.filter(
            tag_type=tt,
            content=self.content).first()

        return ctt.tags.all() if ctt else None

    def get_planning_mag_recommended(self):
        crs = ContentRelationship.objects.filter(content=self.content, relationship="LINKED_PUBLICATION")
        return [cr.content_master_related.content_live for cr in crs]
