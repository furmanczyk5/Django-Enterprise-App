import json
from collections import defaultdict
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import login
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from cm.models.providers import Provider
from consultants.models import Consultant
from content.models import Content
from imis import models as imis_models
from imis.enums.members import ImisMemberTypes
from imis.models import ZipCode
from myapa.models import proxies, Bookmark
from myapa.models.auth import UserAuthorizationToken
from myapa.models.constants import DjangoContactTypes, DjangoOrganizationTypes
from myapa.models.educational_degree import EducationalDegree
from myapa.models.job_history import JobHistory
from myapa.models.proxies import Organization
from uploads.models import DocumentUpload, ImageUpload


def is_authenticated_check_all(request):
    """
    Utility function: Given a request, returns {is_authenticated, username} dictionary if user
    is_authenticated.
    This checks for regular website authentication. If user is not authenticated this way,
    it checks for token authentication.
    """
    # authentication, accounts for mobileapp token authentication too
    if request.method == "GET":
        auth_username = request.GET.get('auth_user_id', '')
        auth_token = request.GET.get('auth_token', '')
        auth_login = request.GET.get('auth_login', '') == "true"
    else:
        auth_username = request.POST.get('auth_user_id', '')
        auth_token = request.POST.get('auth_token', '')
        auth_login = request.POST.get('auth_login', '') == "true"

    is_authenticated = False
    authenticated_username = None

    if request.user.is_authenticated():
        is_authenticated = True
        authenticated_username = request.user

    try_token_authentication = auth_username and \
                               (not is_authenticated or auth_username != request.user)

    if try_token_authentication and UserAuthorizationToken.objects.filter(
            user__username=auth_username,
            token=auth_token
    ).exists():

        # auto login if we get to this case? But don't want to do it for api calls

        if auth_login:
            user = User.objects.filter(username=auth_username).first()
            # user_authenticated = AuthenticationBackend().authenticate(username=auth_username, auto=True)
            login(request, user)

        is_authenticated = True
        authenticated_username = auth_username

    return is_authenticated, authenticated_username


def has_webgroup(user, required_webgroups=[]):
    """
    Simple loop that determines if a passed user has the required webgroup passed in a list.
    Any matching webgroup is valid.
    """

    user_webgroups = user.groups.all()
    is_allowed = False

    for webgroup in required_webgroups:
        if is_allowed:
            break

        for user_webgroup in user_webgroups:
            if user_webgroup.name == webgroup:
                is_allowed = True
                break

    return is_allowed


def individual_fullname(firstname="", lastname="", middle_initial="", suffix="", designation=""):
    _full_title = str(firstname)

    if middle_initial and middle_initial.strip():
        middle_initial = middle_initial.strip()[0].upper()
        _full_title += " %s." % middle_initial

    _full_title += " %s" % lastname

    if suffix and suffix.strip():
        _full_title += " %s" % suffix

    if designation and designation.strip():
        _full_title += ", %s" % designation

    return _full_title


def get_contact_class(contact):
    """
    Determine the correct Contact [proxy] model to use, based on iMIS data

    :param contact: :class:`myapa.models.Contact`
    :return: :class:`myapa.models.Contact`
    """
    if contact.contact_type == DjangoContactTypes.ORGANIZATION.value:
        if contact.member_type == ImisMemberTypes.SCH.value:
            contact_class = proxies.School
        elif contact.organization_type == DjangoOrganizationTypes.CONSULTANT.value:
            contact_class = Consultant
        else:
            contact_class = proxies.Organization
    else:
        contact_class = proxies.IndividualContact
    return contact_class


def get_primary_chapter_code_from_zip_code(zip_code):
    """
    Get the chapter code from a zip code, based on the Zip_Code table in iMIS
    :param zip_code: 5 digit zip code
    :type zip_code: str
    :return: str, chapter code
    """
    zip_five = str(zip_code).strip()[:5]
    zip_record = ZipCode.objects.filter(zip=zip_five).first()
    if zip_record is not None:
        return zip_record.chapter


def duplicate_check(contact=None, first_name=None, last_name=None, birth_date=None,
                    email=None, secondary_email=None, phone=None, secondary_phone=None,
                    cell_phone=None, address1=None, address2=None, city=None, state=None,
                    country=None, zip_code=None, secondary_address1=None,
                    secondary_address2=None, secondary_city=None, secondary_state=None,
                    secondary_country=None, secondary_zip_code=None):
    """
    checks for duplicate users based on point system
    first and last name = 1 point
    primary or additional address = 8 points
    work or home phone number = 8 points
    primary or secondary email addresses = 9 points
    """

    from myapa.models.contact import Contact

    duplicate_scores = defaultdict(int)

    contact_queryset = Contact.objects.filter(contact_type=DjangoContactTypes.INDIVIDUAL.value)
    if contact:
        # later, if we want to run duplicate check on individuals,
        # make an instance method which calls this class method,
        # and pass in the instance using the "contact" kwarg
        contact_queryset = contact_queryset.exclude(id=contact.id)

    if first_name and last_name:

        name_dups = contact_queryset.filter(
            first_name=first_name,
            last_name=last_name
        ).values_list('user__username', flat=True).order_by("user__username").distinct()

        for username in name_dups:
            duplicate_scores[username] += 1

    if birth_date:

        birth_date_dups = contact_queryset.filter(
            birth_date=birth_date
        ).values_list('user__username', flat=True).order_by("user__username").distinct()

        for username in birth_date_dups:
            duplicate_scores[username] += 1

    if email:
        email_dups = contact_queryset.filter(
            email__iexact=email
        ).values_list(
            'user__username',
            flat=True
        ).order_by(
            'user__username'
        ).distinct()

        for username in email_dups:
            duplicate_scores[username] += 9

    if phone or secondary_phone or cell_phone:

        phone_list = [phone] if phone else []
        if secondary_phone:
            phone_list.append(secondary_phone)
        if cell_phone:
            phone_list.append(cell_phone)

        phone_dups = contact_queryset.filter(
            Q(phone__in=phone_list)
            | Q(secondary_phone__in=phone_list)
            | Q(cell_phone__in=phone_list)
        ).values_list('user__username', flat=True).order_by("user__username").distinct()

        for username in phone_dups:
            duplicate_scores[username] += 8

    if address1 or secondary_address1:

        address_dups = contact_queryset.filter(
            Q(address1=address1, address2=address2, city=city,
              state=state, zip_code=zip_code, country=country)
            |
            Q(address1=secondary_address1, address2=secondary_address2,
              city=secondary_city, state=secondary_state, zip_code=secondary_zip_code,
              country=secondary_country
              )
        ).values_list('user__username', flat=True).order_by("user__username").distinct()

        for username in address_dups:
            duplicate_scores[username] += 8

    duplicate_usernames = []
    for username, score in duplicate_scores.items():
        if score >= 9:
            duplicate_usernames.append(username)

    duplicate_contacts = Contact.objects.filter(
        user__username__in=duplicate_usernames
    ).select_related("user")

    return sorted(
        duplicate_contacts,
        key=lambda c: (-duplicate_scores[c.user.username], c.last_name, c.first_name)
    )


def details_delete(request, **kwargs):
    job_id = request.GET.get("job_id", False)
    edu_id = request.GET.get("edu_id", False)
    resume_delete = request.GET.get("resume_delete", False)
    image_delete = request.GET.get("image_delete", False)

    if job_id:
        job = JobHistory.objects.get(id=job_id)
        job.delete()
        messages.success(request, "Your Job details has been removed")
        return redirect(request.META.get('HTTP_REFERER'))

    if edu_id:
        edu = EducationalDegree.objects.get(id=edu_id)
        if edu.seqn:
            imis_models.CustomDegree.objects.filter(seqn=edu.seqn).delete()  # delete from imis too
        edu.delete()
        messages.success(request, "Your Education details has been removed")
        return redirect(request.META.get('HTTP_REFERER'))

    if resume_delete:
        user_docs = DocumentUpload.objects.filter(
            upload_type__code="RESUMES", created_by=request.user
        )
        user_docs[0].delete()
        messages.success(request, "Your Resume has been removed")
        return redirect(request.META.get('HTTP_REFERER'))

    if image_delete:
        user_images = ImageUpload.objects.filter(
            upload_type__code="PROFILE_PHOTOS",
            created_by=request.user
        )
        user_images[0].delete()
        messages.success(request, "Your Profile Image has been removed")
        return redirect(request.META.get('HTTP_REFERER'))


@csrf_exempt
def bookmark(request, **kwargs):
    """
    simple method-based view to add/remove bookmarks
    """
    if request.user.is_authenticated():
        action = request.GET.get("action", "create")
        redirect_option = request.GET.get("redirect", "False")
        contact = request.contact
        try:
            content = Content.objects.filter(
                master__id=kwargs.get("master_id", None),
                publish_status="PUBLISHED"
            ).first()
            if action == "create":
                bookmark, created = Bookmark.objects.get_or_create(
                    content=content,
                    contact=contact
                )
            elif action == "delete":
                bookmark = get_object_or_404(Bookmark, content=content, contact=contact)
                bookmark.delete()
                if redirect_option == 'True':
                    return redirect(request.META.get('HTTP_REFERER'))
            return HttpResponse(
                json.dumps({"success": True, "action": action}),
                content_type='application/json'
            )
        except Exception as e:
            return HttpResponse(
                json.dumps({"success": False, "error": str(e)}),
                content_type='application/json'
            )
    else:
        # TO DO... how to handle this messaging?
        return HttpResponse(
            json.dumps({"success": False, "error": "not authenticated"}),
            content_type='application/json'
        )


class DuplicateCheck(object):
    def __init__(self, **kwargs):

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.all_candidates = []
        self.default_query_kwargs = dict()

    def set_candidates(self):
        pass

    def get_candidates(self):
        return self.all_candidates

    def get_string_for_icontains_search(self, attribute, start_idx=1, end_idx=-1):
        """
        Get a string for searching a database with the
        :class:`django.db.models.lookups.IContains` operator.

        This method is extremely simple for now - it simply returns a string between
        the start_idx and end_idx parameters (1 and -1 by default) to try to correct for
        plurals, typos, or conventions of standardized string formats like URLs. For example:

        "Clarion Associates" -> "larion Associate"

        If you want to try to match URLs that start with http:// or http://www.
        >>> dc = DuplicateCheck(personal_url='http://www.clarionassociates.com')
        >>> dc.get_string_for_icontains_search(attribute='personal_url', start_idx=dc.personal_url.find('://') + 7)  # the 7 offsets the start of ://www.
        'clarionassociates.co'


        In the future, we should consider enhancing this method with things like
        - thresholds of total string length for determining how much to chop off
        - how to handle common abbreviation suffixes like LLC, LLP, Inc, etc.

        :param attribute: str, the attribute on this class (passed in as a kwarg when instantiating)
                          to get the string for searching
        :param start_idx: int, the start index of the string
        :param end_idx: int, the end index of the string (use negative indexing - i.e. this number
                        of spaces from the end)
        :return: str
        """
        if not isinstance(attribute, str):
            raise TypeError('`attribute` must be a string, not {}'.format(type(attribute)))
        attr = getattr(self, attribute, '').strip()
        if not attr:
            return ''
        return attr[start_idx:end_idx]

    def check_email(self):
        if getattr(self, "email", None) is not None:
            self.all_candidates.extend([
                x for x in imis_models.Name.objects.filter(
                    email__iexact=self.email,
                    **self.default_query_kwargs
                )
            ])


class OrgDupeCheck(DuplicateCheck):

    def __init__(self, **kwargs):
        super(OrgDupeCheck, self).__init__(**kwargs)

        # TODO: Do we want to do this? Could help reduce query
        # time but might miss records erroneously tagged as member_record
        self.default_query_kwargs = dict(
            company_record=True
        )
        self.company_name_candidates = []
        self.url_candidates = []
        self.location_candidates = []
        self.ein_candidates = []
        self.set_candidates()

    def set_candidates(self):
        self.all_candidates = defaultdict(dict)

        self.check_company_name()
        self.check_location()
        self.check_url()
        self.check_ein_number()

    def get_all_candidates(self):
        candidates = []
        for x in self.all_candidates:
            data = {
                'id': x,
                'company': self.all_candidates[x].get('company', ''),
                'website': self.all_candidates[x].get('website', ''),
                'full_address': self.all_candidates[x].get('full_address', '')
            }
            candidates.append(data)
        return candidates

    def check_company_name(self):
        if getattr(self, "company", None) is not None:
            company = self.company
            if len(self.company) <= 6:
                self.company_name_candidates = imis_models.Name.objects.filter(
                    company__iexact=company,
                    **self.default_query_kwargs
                ).exclude(
                    id=getattr(self, 'id', '')
                )
            else:
                self.company_name_candidates = imis_models.Name.objects.filter(
                    company__icontains=self.get_string_for_icontains_search('company'),
                    **self.default_query_kwargs
                ).exclude(
                    id=getattr(self, 'id', '')
                )
            for x in self.company_name_candidates:
                self.all_candidates[x.id]['company'] = x.company

    def check_url(self):
        url = getattr(self, 'personal_url', None)
        if not isinstance(url, str) or not url.strip():
            return
        parsed = urlparse(url)
        netloc = parsed.netloc.replace('www.', '')
        if netloc:
            self.url_candidates = imis_models.Name.objects.filter(
                website__icontains=netloc,
                **self.default_query_kwargs
            )
            for x in self.url_candidates:
                if self.all_candidates.get(x.id, {}).get('company'):
                    self.all_candidates[x.id]['website'] = x.website

    def check_ein_number(self):
        """
        Check for other organizations with the same EIN and flag it in the email to AICP team
        :return: :class:`django.db.models.query.QuerySet`
        """
        if not isinstance(getattr(self, "ein_number", None), str):
            return
        ein_queries = Provider.get_ein_query(self.ein_number)
        self.ein_candidates = Organization.objects.filter(
            ein_number__in=ein_queries
        ).exclude(
            user__username=getattr(self, 'id', '')
        )
        for x in self.ein_candidates:
            self.all_candidates[x.id]['ein_number'] = x.ein_number

    def check_location(self):
        fields = [
            'address1',
            'city',
            'state',
            'zip_code'
        ]

        # Only run the search if instantiated with the required fields
        intersection = set.intersection(set(fields), set(dir(self)))
        if sorted(list(intersection)) != sorted(list(fields)):
            return

        # Only run the search if names already matched (obviously, could
        # be many organizations in one large office building with the
        # same address)
        if self.company_name_candidates:
            self.location_candidates = imis_models.NameAddress.objects.filter(
                id__in=[x.id for x in self.company_name_candidates],
                state_province=self.state,
                zip__icontains=self.get_string_for_icontains_search('zip_code'),
                city__icontains=self.get_string_for_icontains_search('city'),
                address_1__icontains=self.get_string_for_icontains_search(
                    attribute='address1',
                    start_idx=3,
                    end_idx=-3
                ),
            )
            for x in self.location_candidates:
                self.all_candidates[x.id]['full_address'] = '{}, {}, {}, {}'.format(
                    self.address1, self.city, self.state, self.zip_code
                )
                self.all_candidates[x.id]['company'] = x.company


def dict_diff(dict1, dict2):
    return {k: dict1[k] for k in dict1 if k in dict2 and dict1[k] != dict2[k]}
