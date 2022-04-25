from django.shortcuts import render

from imis.enums.relationship_types import ImisRelationshipTypes
from imis.models import Relationship
from myapa.models.proxies import Organization
from myapa.viewmixins import AuthenticateLoginMixin


class AuthenticateOrganizationAdminMixin(AuthenticateLoginMixin):
    """
    Restricts access only if the logged-in user is an administrator of the linked organization
    """

    def __init__(self):
        super(AuthenticateLoginMixin, self).__init__()
        self.relationships = None
        self.organization = None
        self.user_is_admin = False
        self.user_is_cm_admin = False
        self.is_cm_provider = False

    def authenticate(self, request, *args, **kwargs):
        authentication_response = super().authenticate(request, *args, **kwargs)
        if authentication_response is not None:
            return authentication_response
        else:
            self.get_organization_admin()

            # Both ADMIN_I and CM_I can access My Org dashboard
            if self.organization and (self.user_is_admin or self.user_is_cm_admin):
                return None
            else:
                return render(
                    request,
                    "myapa/newtheme/restricted-access.html",
                )

    def get_organization_admin(self):

        self.relationships = Relationship.objects.filter(
            id=self.request.user.username,
            relation_type__in=(
                ImisRelationshipTypes.ADMIN_I.value,
                ImisRelationshipTypes.CM_I.value
            )
        )
        if self.relationships.exists():
            self.organization = Organization.objects.filter(
                    user__username__in=[x.target_id for x in self.relationships]
                ).order_by(
                    'updated_time'
                ).last()
            self.user_is_admin = self.relationships.filter(
                relation_type=ImisRelationshipTypes.ADMIN_I.value
            ).exists()
            self.user_is_cm_admin = self.relationships.filter(
                relation_type=ImisRelationshipTypes.CM_I.value
            )
