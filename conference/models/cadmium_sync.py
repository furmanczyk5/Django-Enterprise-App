import datetime
import pytz
import requests
from decimal import Decimal
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q

from conference.models import NationalConferenceActivity
from content.models import TagType, Tag, TaxoTopicTag, ContentTagType, MasterContent
from events.models import Activity, NATIONAL_CONFERENCE_NEXT
from myapa.models import Contact
from myapa.models.contact_role import ContactRole
from myapa.models.profile import IndividualProfile
from pages.models import LandingPageMasterContent
from uploads.models import UploadType, ImageUpload


def try_to_get(func):
    """
    Decorator to wrap CadmiumSync get methods in try/except.
    call method with context-specific return value, e.g. get_val(dict, 0)
    :param func:the wrapped function
    :obj_dict: the data dict from Cadmium
    :default_return_val: specific value to return if it bombs out
    :return:
    """
    def try_wrapper(self, obj_dict, default_return_val):
        try:
            return func(self, obj_dict)
        except Exception as e:
            print("EXCEPTION calling %s: %s" % (func.__name__, e))
            return default_return_val
    return try_wrapper


class CadmiumSync(models.Model):
    """
    A CadmiumSync record represents a sync between a Conference in Django and
    a presentation in Cadmium
    """
    mappings = models.ManyToManyField(
        "conference.CadmiumMapping", through='conference.SyncMapping', related_name="harvester_syncs")

    microsite = models.ForeignKey("conference.Microsite", on_delete=models.SET_NULL,
                                  related_name="cadmium_sync", blank=True, null=True)
    cadmium_event_key = models.CharField(
        max_length=200, null=True, blank=True, db_index=True)
    registration_task_id = models.CharField(max_length=20, null=True, blank=True)
    endpoint = models.URLField(max_length=255, blank=True, null=True)
    # parent landing master id for Django events' landing page
    parent_landing_master_id = models.IntegerField(null=True, blank=True)
    track_tag_type_code = models.CharField(max_length=200, null=True, blank=True)
    activity_tag_type_code = models.CharField(max_length=200, null=True, blank=True)
    division_tag_type_code = models.CharField(max_length=200, null=True, blank=True)
    npc_category_tag_type_code = models.CharField(max_length=200, null=True, blank=True)

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Cadmium Sync Setup for %s" % (self.microsite if self.microsite else "<No Microsite Assigned>")

    def get_api_key(self):
        if not self.cadmium_event_key:
            return None
        else:
            return settings.CADMIUM_API_KEYS.get(self.cadmium_event_key)

    def get_conference_timezone(self):
        multi_event = self.microsite.event_master.content_draft.event
        return pytz.timezone(multi_event.timezone)

    @try_to_get
    def get_location(self, obj_dict):
        mapping_to_location = self.mappings.filter(
            to_string="location"
        ).first()
        cadmium_field_name = mapping_to_location.from_string
        event_location = obj_dict[cadmium_field_name].strip()
        room = obj_dict["PresentationRoom"].strip()
        a = bool(event_location)
        b = bool(room)
        if a ^ b:
            return event_location or room
        elif a & b:
            return event_location + " " + room if event_location is not room else room
        else:
            return None

    @try_to_get
    def build_full_text_html(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="text").first()
        cadmium_field_name = mapping.from_string
        long_description = '<p>' + obj_dict[cadmium_field_name].strip() + '</p>'
        fhs = formatted_html_string = '<html><head></head><body>'
        fhs = fhs + '<h3 class="headline-underline">MORE SESSION DETAILS</h3>'
        fhs = fhs + long_description
        fhs = fhs + '</body></html>'
        return fhs

    @try_to_get
    def get_learning_objectives(self, obj_dict):
        e = obj_dict
        los = learning_objectives = ""
        for i in range(1, 11):
            learning_objective_key = "LearningObjective%s" % i
            if e[learning_objective_key]:
                los = los + '<li>' + e[learning_objective_key] + '</li>'
        if los:
            los = '<ul>' + los + '</ul>'
            return los
        else:
            return ''

    @try_to_get
    def get_parent(self, obj_dict):
        # return MasterContent.objects.get(content_live__code=NATIONAL_CONFERENCE_NEXT[0])
        return getattr(self.microsite,'event_master',None)

    @try_to_get
    def get_parent_landing_master(self, obj_dict):
        event_landing_page = LandingPageMasterContent.objects.get(id=self.parent_landing_master_id)
        return event_landing_page

    @try_to_get
    def get_cm_status(self, obj_dict):
        credits = float(obj_dict["Presentationcehours"])
        return 'A'

    @try_to_get
    def get_cm(self, obj_dict):
        credits = float(obj_dict["Presentationcehours"])
        return credits

    @try_to_get
    def get_cm_law_approved(self, obj_dict):
        mapping_to_cm_law_approved = self.mappings.filter(
            to_string="cm_law_approved"
        ).first()
        cadmium_field_name = mapping_to_cm_law_approved.from_string
        cm_law_approved = float(obj_dict[cadmium_field_name].strip())

        return cm_law_approved or 0

    # @try_to_get
    # def get_cm_ethics_requested(self, obj_dict):
    #     mapping = self.mappings.filter(
    #         to_string="cm_ethics_requested"
    #     ).first()
    #     fromzi = mapping.from_string
    #     return float(obj_dict[fromzi].strip()) or 0

    @try_to_get
    def get_cm_ethics_approved(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="cm_ethics_approved"
        ).first()
        fromzi = mapping.from_string
        return float(obj_dict[fromzi].strip()) or 0

    @try_to_get
    def get_keywords(self, obj_dict):
        mappings = self.mappings.filter(
            to_string="keywords"
        ).order_by("from_string")
        cadmium_topic_strings = [obj_dict[mapping.from_string] for mapping in mappings]

        if len(cadmium_topic_strings) == 1:
            keyword_text = cadmium_topic_strings[0]
        elif len(cadmium_topic_strings) > 1:
            keyword_text = ", ".join(cadmium_topic_strings)
        else:
            keyword_text = ""

        if keyword_text != "":
            s = keyword_text
            tokens = [x.strip() for x in s.split(',')]
            token_set = set(tokens)
            keywords = ", ".join(token_set)
        else:
            keywords = ""

        if keywords != "":
            return keywords
        else:
            return None

    @try_to_get
    def get_status(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="status"
        ).first()
        cadmium_code = obj_dict[mapping.from_string].strip()
        status_code = 'H' if cadmium_code == 'H' else 'A'
        return status_code

    @try_to_get
    def get_role_type(self, obj_dict):
        field_mapping = self.mappings.filter(
            to_string="role_type"
        ).first()
        cadmium_role = obj_dict[field_mapping.from_string].strip()
        datum_mapping = self.mappings.filter(
            from_string=cadmium_role
        ).first()
        django_role = datum_mapping.to_string
        return django_role

    @try_to_get
    def get_begin_time(self, obj_dict):
        tz = self.get_conference_timezone()
        mapping = self.mappings.filter(
            to_string="begin_time"
        ).first()
        begin_time_str = obj_dict[mapping.from_string].strip()
        begin_time_dt = tz.localize(datetime.datetime.strptime(begin_time_str, "%Y-%m-%dT%H:%M:%S"))
        return begin_time_dt

    @try_to_get
    def get_end_time(self, obj_dict):
        tz = self.get_conference_timezone()
        mapping = self.mappings.filter(
            to_string="end_time"
        ).first()
        end_time_str = obj_dict[mapping.from_string].strip()
        end_time_dt = tz.localize(datetime.datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S"))
        return end_time_dt

    @try_to_get
    def get_outside_vendor(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="outside_vendor"
        ).first()
        has_outside_vendor = obj_dict[mapping.from_string].strip()
        has_outside_vendor = True if has_outside_vendor == "True" else False
        return has_outside_vendor

    @try_to_get
    def get_track_tags(self, e):
        li = []
        track_tag_title = e["TrackName"]
        mapping = self.mappings.filter(
            mapping_type="HARVESTER_TRACK_TO_APA_CODE",
            from_string=track_tag_title
        ).first()
        track_tag_code = mapping.to_string.strip()
        t = Tag.objects.get(code=track_tag_code)
        li.append(t)
        print("track tag list is ", li)
        return li

    @try_to_get
    def get_activity_type_tag(self, e):
        li = []
        activity_tag_title = e["CourseName"].strip()
        mapping = self.mappings.filter(
            Q(from_string=activity_tag_title) | Q(from_string=activity_tag_title[:-1]),
            mapping_type="HARVESTER_SESSION_TYPE_TO_ACTIVITY_TYPE"
        ).first()
        activity_tag_code = mapping.to_string.strip()
        t = Tag.objects.filter(code=activity_tag_code).first()
        if not t:
            activity_tag_code = "SESSION"
            t = Tag.objects.get(code=activity_tag_code)
        li.append(t)
        print("activity type tag list is ", li)
        return li

    @try_to_get
    def get_division_tags(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="division_tags"
        ).first()
        # this is a string of Tag titles, not codes
        s = division_tag_codes_string = obj_dict[mapping.from_string].strip()
        tags = []
        division_tag_type = TagType.objects.get(code='DIVISION')
        dtt = division_tag_type

        if len(s) > 0:
            tokens = [x.strip() for x in s.split(',')]
            tag_codes = sorted(tokens)
            # FLAGGED FOR REFACTORING: CADMIUM SYNC
            # We need to query on title here not code
            # tags = [Tag.objects.get(code=tc, tag_type=dtt) for tc in tag_codes]
            tags = [Tag.objects.get(title=tc, tag_type=dtt) for tc in tag_codes]
            print("division tags are ", tags)
        return tags

    @try_to_get
    def get_topic_tags(self, obj_dict):
        tag_codes = []
        mapping = self.mappings.filter(
            to_string="topic_tags"
        ).first()
        topic_names_string = obj_dict[mapping.from_string].strip()
        topics = [d.get("from_string") for d in self.mappings.filter(
                        mapping_type="HARVESTER_TOPICS_TO_APA_TAXO"
                    ).values("from_string")]
        for t in topics:
            if topic_names_string.find(t) >= 0:
                mapping = self.mappings.filter(
                    from_string=t,
                    mapping_type="HARVESTER_TOPICS_TO_APA_TAXO"
                ).first()
                tag_code = mapping.to_string.strip()
                tag_codes.append(tag_code)
        tags = list(set([TaxoTopicTag.objects.get(code=tc) for tc in tag_codes]))
        print("taxo topic tags are ", tags)
        return tags

    @try_to_get
    def get_streaming_tag(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="streaming_tag"
        ).first()
        streaming_answer = obj_dict[mapping.from_string].strip()
        streaming = True if streaming_answer == "Yes" else False

        if streaming:
            li = []
            streaming_tag_code = "STREAMING"
            streaming_tag = Tag.objects.get(code=streaming_tag_code)
            li.append(streaming_tag)
            return li
        else:
            return []

    @try_to_get
    def get_zoom_link(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="zoom_link"
        ).first()
        zoom_link = obj_dict[mapping.from_string].strip()
        return zoom_link

    @try_to_get
    def get_recorded_tag(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="recorded_tag"
        ).first()
        recorded_answer = obj_dict[mapping.from_string].strip()
        recorded = True if recorded_answer == "Yes" else False

        if recorded:
            li = []
            recorded_tag_code = "RECORDED_SESSION"
            recorded_tag = Tag.objects.get(code=recorded_tag_code)
            li.append(recorded_tag)
            return li
        else:
            return []

    @try_to_get
    def get_local_tag(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="local_tag"
        ).first()
        local_answer = obj_dict[mapping.from_string].strip()
        local = True if local_answer == "Yes" else False

        if local:
            li = []
            local_tag_code = "LOCAL"
            local_tag = Tag.objects.get(code=local_tag_code)
            li.append(local_tag)
            return li
        else:
            return []

    @try_to_get
    def get_interactive_tag(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="interactive_tag"
        ).first()
        interactive_answer = obj_dict[mapping.from_string].strip()
        interactive = True if interactive_answer == "Yes" else False

        if interactive:
            li = []
            interactive_tag_code = "INTERACTIVE"
            interactive_tag = Tag.objects.get(code=interactive_tag_code)
            li.append(interactive_tag)
            return li
        else:
            return []

    @try_to_get
    def get_food_tag(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="food_tag"
        ).first()
        food_answer = obj_dict[mapping.from_string].strip()
        food = True if food_answer == "Yes" else False

        if food:
            li = []
            food_tag_code = "FOOD_INCLUDED"
            food_tag = Tag.objects.get(code=food_tag_code)
            li.append(food_tag)
            return li
        else:
            return []

    @try_to_get
    def get_learn_tag(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="learn_tag"
        ).first()
        learn_answer = obj_dict[mapping.from_string].strip()
        learn = True if learn_answer == "Yes" else False

        if learn:
            li = []
            learn_tag_code = "APA_LEARN"
            learn_tag = Tag.objects.get(code=learn_tag_code)
            li.append(learn_tag)
            return li
        else:
            return []

    @try_to_get
    def get_max_quantity(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="max_quantity"
        ).first()
        quantity = Decimal(obj_dict[mapping.from_string].strip())
        if not quantity:
            quantity = Decimal('1.00')
        return quantity

    # Actually, it looks like we may need to keep this because we may be
    # treating max_quantity_standby as a boolean (>0 equals standby allowed)
    @try_to_get
    def get_max_quantity_standby(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="max_quantity_standby"
        ).first()
        quantity = Decimal(obj_dict[mapping.from_string].strip())
        if not quantity:
            quantity = Decimal('1.00')
        return quantity

    @try_to_get
    def get_max_quantity_per_person(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="max_quantity_per_person"
        ).first()
        quantity = Decimal(obj_dict[mapping.from_string].strip())
        if not quantity:
            quantity = Decimal('1.00')
        return quantity

    @try_to_get
    def get_price(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="price"
        ).first()
        price = Decimal(obj_dict[mapping.from_string].strip())
        return price

    @try_to_get
    def get_imis_code(self, obj_dict):
        django_multi_event_code = self.microsite.event_master.content_live.code
        return django_multi_event_code + "/" + obj_dict["PresentationNumber"]

    @try_to_get
    def get_gl_account(self, obj_dict):
        mapping = self.mappings.filter(
            to_string="gl_account"
        ).first()
        gl_account = obj_dict[mapping.from_string].strip()
        return gl_account

    def field_to_field(self, django_obj, cadmium_mapping, api_obj):
        from_field = cadmium_mapping.from_string
        to_field = cadmium_mapping.to_string
        setattr(django_obj, to_field, api_obj[from_field])

    def update_presentation(self, calling_obj, obj_dict):
        from conference.views.harvester import UpdatePresentation

        context = {}
        e = obj_dict
        is_streaming = e["CustomPresField42"] == 'Yes'

        # FOR TESTING ONLY:
        print("is_streaming is ", is_streaming)
        print("Activity code is ", e["PresentationNumber"])
        # if is_streaming and e["PresentationNumber"] == 'NPCH208063':
        if is_streaming:
            if type(calling_obj) == type(UpdatePresentation()):
                external_key = calling_obj.kwargs.get("external_key")
            elif type(calling_obj) == type(NationalConferenceActivity()) or type(calling_obj) == type(Activity()):
                external_key = calling_obj.external_key
            else:
                external_key = e["PresentationID"]

            activities = Activity.objects.filter(
                external_key=external_key,
                publish_status="DRAFT",
                )

            if activities.count() > 1:
                raise Exception("Error: More than one Draft Activity record found.")
            else:
                activity = activities.first()

            created = False
            if not activity:
                # FLAGGED FOR REFACTORING: CADMIUM SYNC
                if getattr(self.microsite, 'is_npc', False):
                    activity = NationalConferenceActivity.objects.create(
                        external_key=external_key,
                        publish_status="DRAFT",
                        )
                else:
                    activity = Activity.objects.create(
                        external_key=external_key,
                        publish_status="DRAFT",
                        )
                created=True
            print("\nSTART ******************")
            print("Activity master id is ", activity.master_id)
            self.update_activity(activity, e)
            self.update_tags(activity, e)
            self.update_product(activity, e)
            self.update_contact_roles(activity, e)

            activity.taxo_topic_tags_save()
            # FORCE HIDING WHEN RUNNING MASS SYNC PRE-LAUNCH
            # COMMENT OUT AND RUN SCRIPT TO UNHIDE ALL AS PART OF SOFT LAUNCH
            # activity.status = 'H'
            activity.save()
            published_activity = activity.publish()
            published_activity.solr_publish()

            context["master_id"] = activity.master_id
            context["success"] = True

            if created:
                context["message"] = "Successfully created event."
            else:
                context["message"] = "Successfully updated event."
            print("END *************\n")
        else:
            context["success"] = True
            context["message"] = "Not a NPC20 at Home streaming event. No action taken."
        return context

    def update_activity(self, activity, obj_dict):
        e = obj_dict
        cm = self.get_cm(e,0)

        activity.learning_objectives=self.get_learning_objectives(e,'')
        activity.text=self.build_full_text_html(e,None)
        activity.begin_time=self.get_begin_time(e,None)
        activity.end_time=self.get_end_time(e,None)
        activity.timezone=self.get_conference_timezone()
        activity.location=self.get_location(e,None)
        activity.code=e["PresentationNumber"]
        activity.title=e["PresentationTitle"]
        activity.description=e["AbstractTextShort"][0:400]
        activity.status = self.get_status(e,'A')
        activity.keywords=self.get_keywords(e,None)
        activity.cm_status=self.get_cm_status(e,'I')
        activity.cm_approved=Decimal(cm)
        activity.cm_law_approved=Decimal(self.get_cm_law_approved(e,0))
        activity.cm_ethics_approved=Decimal(self.get_cm_ethics_approved(e,0))
        activity.resource_url=self.get_zoom_link(e,None)
        # .parent overridden on model save() BUT ONLY IF .parent is None
        # overridden here: conference/models/microsite_activity.py
        # THIS WORKED LOCALLY BUT NOT ON STAGING
        # if activity.parent:
        #     parent_from_method = self.get_parent(e,None)
        #     if parent_from_method:
        #         activity.parent = parent_from_method
        parent_from_method = self.get_parent(e,None)
        # if self.microsite and not self.microsite.is_npc:
        #     activity.parent = parent_from_method
        # i don't see how this can exist before sync_to_imis unless we do it here
        activity.parent = parent_from_method
        activity.outside_vendor=self.get_outside_vendor(e,False)
        activity.parent_landing_master = self.get_parent_landing_master(e,None)
        activity.save()

    def update_tags(self, activity, obj_dict):
        e = obj_dict
        # try/except this to allow some syncs not to have certain parts of this tagging:
        try:
            track_tag_type = TagType.objects.get(code=self.track_tag_type_code)
            activity_tag_type = TagType.objects.get(code=self.activity_tag_type_code)
            division_tag_type = TagType.objects.get(code=self.division_tag_type_code)
            npc_category_tag_type = TagType.objects.get(code=self.npc_category_tag_type_code)
        except Exception as ex:
            print("Exception getting tag types: ", ex)

        track_tags = self.get_track_tags(e,[])
        activity_tag = self.get_activity_type_tag(e,[])
        division_tags = self.get_division_tags(e,[])
        topic_tags = self.get_topic_tags(e,[])
        npc_category_tags = self.get_streaming_tag(e,[]) + self.get_recorded_tag(e,[]) + \
            self.get_local_tag(e,[]) + self.get_food_tag(e,[]) + self.get_interactive_tag(e,[]) + \
            self.get_learn_tag(e,[])

        ttt=att=dtt=ntt=None
        if track_tags:
            ttt, ttt_created = ContentTagType.objects.get_or_create(tag_type=track_tag_type, content=activity)
        if activity_tag:
            att, att_created = ContentTagType.objects.get_or_create(tag_type=activity_tag_type, content=activity)
        if division_tags:
            dtt, dtt_created = ContentTagType.objects.get_or_create(tag_type=division_tag_type, content=activity)
        if npc_category_tags:
            ntt, ntt_created = ContentTagType.objects.get_or_create(tag_type=npc_category_tag_type, content=activity)

        if ttt and track_tags:
            ttt.tags.set(track_tags)
        if att and activity_tag:
            att.tags.set(activity_tag)
        if dtt and division_tags:
            dtt.tags.set(division_tags)
        # MUST SET TAXO TAGS DIRECTLY
        activity.taxo_topics.set(topic_tags)
        if ntt and npc_category_tags:
            ntt.tags.set(npc_category_tags)

    def update_product(self, activity, obj_dict):
        from store.models import Product, ProductPrice
        e = obj_dict
        price = self.get_price(e,None)

        if price is not None:
            pr, pr_created = Product.objects.get_or_create(
                content=activity,
                publish_status='DRAFT')
            if pr:
                pr.code=e["PresentationNumber"]
                pr.imis_code = self.get_imis_code(e,None)
                pr.gl_account = self.get_gl_account(e,None)
                pr.max_quantity=self.get_max_quantity(e,Decimal('1.00'))
                pr.max_quantity_standby=self.get_max_quantity_standby(e,Decimal('1.00'))
                pr.max_quantity_per_person=self.get_max_quantity_per_person(e,Decimal('1.00'))
                pr.description=e["AbstractTextShort"][0:400]
                pr.save()

                prpr, prpr_created = ProductPrice.objects.get_or_create(
                    product=pr)

                prpr.title="Cost"
                prpr.include_search_results = True
                prpr.price=price
                prpr.save()

        activity.sync_to_imis()


    def update_contact_roles(self, activity, obj_dict):
        e = obj_dict
        seen_roles =[]
        context = {"message": "Nothing happened"}
        speakers_dict_list = e["Presenters"]
        i = 0

        if speakers_dict_list:
            context = {}
            for speaker_dict in speakers_dict_list:
                # NEED THIS TRY/EXCEPT AT MINIMUM FOR LOCAL TESTING
                # cuz contacts on prod may not be on local yet
                try:
                    s = speaker_dict
                    role_type = self.get_role_type(s,"SPEAKER")

                    if role_type != "SUBMITTER" and role_type != "ORGANIZER":
                        username = s["PresenterMemberNumber"].strip()
                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        print("USERNAME FROM CADMIUM IS .... ?? ", username)
                        speaker = Contact.objects.get(user__username=username)
                        self.update_contact(speaker, s)
                        speaker_role, sr_created = ContactRole.objects.get_or_create(
                            content=activity, contact=speaker, role_type=role_type)
                        speaker_role.confirmed = True
                        speaker_role.save()
                        # ASSEMBLE LIST OF SPEAKERS WHO SHOULD BE DELETED:
                        seen_roles.append(speaker_role)
                        # seen_role_ids = [cr.id for cr in seen_roles]
                        # django_roles = ContactRole.objects.filter(content=activity).exclude(id__in=seen_role_ids)
                        i += 1
                        context_string = "speaker%s" % i
                        context[context_string] = "%s (%s)" % (speaker, speaker.user.username)
                        # context[context_string] = "%s (%s) is a %s." % (speaker, speaker.user.username, speaker_role.role_type)
                except Exception as e:
                    print("ERROR WITH SPEAKER: " + str(e))
            seen_role_ids = [cr.id for cr in seen_roles]
            django_roles = ContactRole.objects.filter(content=activity).exclude(id__in=seen_role_ids)
            django_roles.delete()
            # FLAGGED FOR REFACTORING: SPEAKER DELETE
            draft_role_publish_uuids = ContactRole.objects.filter(content=activity).values('publish_uuid')
            draft_publish_uuids = [v.get('publish_uuid') for v in draft_role_publish_uuids]
            published_event = activity.get_versions().get('PUBLISHED')

            if published_event:
                published_contact_roles = ContactRole.objects.filter(content=published_event)

                for s in published_contact_roles:

                    if s.publish_uuid not in draft_publish_uuids:
                        s.delete()

        return context

    def update_contact(self, contact, speaker_dict):
        s = speaker_dict

        company = s["PresenterOrganization"][0:80]
        job_title = s["PresenterPosition"][0:80]
        email = s["PresenterEmail"]
        user_data = {
            "company": company,
            "job_title": job_title,
            "email": email,
        }
        name = contact.get_imis_name()
        if name is not None:
            name.__dict__.update(user_data)
            name.save()

        contact.company = company
        contact.job_title = job_title
        contact.email = email
        contact.external_id=s["PresenterID"]
        contact.bio = s["PresenterBiographyText"]
        contact.about_me = s["PresenterBioSketchText"]
        contact.personal_url=s["PresenterWebsite"]
        contact.twitter_url=s["PresenterTwitter"]
        contact.facebook_url=s["PresenterFacebook"]
        contact.linkedin_url=s["PresenterLinkedIn"]
        contact.instagram_url=s["PresenterInstagram"]
        photo_url = s["PresenterPhotoFileName"]
        if photo_url:
            name = urlparse(photo_url).path.split('/')[-1]
            response = requests.get(photo_url)
            upload_type_profile_photo = UploadType.objects.get(code='PROFILE_PHOTOS')
            image_upload_instance = ImageUpload(upload_type=upload_type_profile_photo)
            if response.status_code == 200:
                image_upload_instance.image_file.save(name, ContentFile(response.content), save=True)
                IndividualProfile.objects.get_or_create(contact=contact)
                contact.individualprofile.image = image_upload_instance
                contact.individualprofile.save()
        contact.save()

    def delete_presentation(self, view):
        external_key = view.kwargs.get("external_key")
        activity = Activity.objects.get(
            external_key=external_key,
            publish_status="DRAFT",
            )
        activity.status = 'X'
        activity.save()
        published_activity = activity.publish()
        published_activity.solr_publish()

    def update_presenter(self, view, obj_dict):
        external_id = view.kwargs.get("external_id")
        s = obj_dict
        context = {}

        if external_id == s["PresenterID"]:
            username = s["PresenterMemberNumber"].strip()
            speaker = Contact.objects.get(
                user__username=username,
            )
            self.update_contact(speaker, s)
            context["success"] = True
            context["message"] = "Successfully added/updated speaker info."
        else:
            context["success"] = False
            context["message"] = "Error: Could not add/update speaker info."

        return context

