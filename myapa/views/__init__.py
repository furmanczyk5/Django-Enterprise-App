from .account import MyapaOverviewView, MyapaAccountFormView, MyapaAddressesFormView, \
    MyapaPersonalInformationFormView, PublicProfileView, EditProfileView, ProfileShareView, \
    UpdateSocialLinksView, UpdateBioAndAboutMe, ContactPreferencesUpdateView, \
    EventsAttendedView, EducationView, JobHistoryView, OrderHistoryView, \
    BookmarksView, AICPStatusView, UpdateProfileImageView, CreateAccountFormViewMixin, ResumeUploadView
from myapa.utils import details_delete, bookmark
from myapa.views.account import del_additional_address, generate_url

from .admin import CreateDjangoUserView, admin_update_groups, MergeCheckView

from .authentication import UserLogin, ResetPasswordView, AutoLoginViaMobile, \
    ComponentUserLogin, login_as_user, login_mobile, logout_mobile, get_contact_mobile, overdrive_access, \
    planning_mag_access, planning_mag_create_user, ProposalsSsoView, ProposalsSsoUserDataView, ProposalsSsoLoginView, \
    EngageSsoLoginView, LearnSsoView, SurveyBallotSystemsRedirectView, OpenWaterSsoLoginView, OpenWaterSsoLoginPart2View

from .freestudents import FreeStudentAdminRouteSchool, FreeStudentAdminDashboard, FreeStudentAdminEditStudentFormView, \
    FreeStudentAdminDeleteStudentFormView

from .join import JoinAccountView, JoinPersonalInformationView, \
    JoinEnhanceMembershipView, JoinMembershipSummaryView, NonMemberJoinView, \
    StudentJoinAccountView, StudentJoinSchoolInformationView, \
    StudentJoinPersonalInformationView, StudentJoinEnhanceMembershipView, \
    StudentJoinMembershipSummaryView, StudentJoinConfirmationView, StudentUpdateDivisionsView, \
    MembershipCartViewMixin

from myapa.views.myorg.contacts import MyOrganizationContactsView
from myapa.views.myorg.addresses import MyOrganizationAddressesView
from myapa.views.myorg.dashboard import MyOrganizationDashboardView
from myapa.views.myorg.eval_data import MyOrganizationEvalDataDownloadView


from .api import ApiGetContactView, ApiSearchContactsView, \
    ApiGetScheduleView, ApiUpdateScheduleView, ApiLoginView, MobileSsoView, \
    HigherLogicApiLoginView, ApiCMTrackerCreateView


# SHOULD MOVE CODE BELOW TO conference or events app
from django.contrib import messages
from django.shortcuts import redirect
from content.mail import Mail
from myapa.models.contact import Contact

# Should move this to evnets or conference app
def resend_mail_invite(request, *args, **kwargs):
    try:
        contact = Contact.objects.get(user__username=args[0])
    except Contact.DoesNotExist:
        contact = None
    if contact is not None and contact.email:
        Mail.send('CONFERENCE_SPEAKER_INVITE', contact.email)
        messages.success(request, 'Conference Invite resent successfully.')

    else:
        messages.success(request, 'Problem with resending invite. Please check the contact details.')

    return redirect(request.META.get('HTTP_REFERER'))
