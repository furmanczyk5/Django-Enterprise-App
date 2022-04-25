from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password

from myapa.models.contact import Contact
from myapa.permissions import utils


class AuthenticationBackend(object):
    """
    Custom APA authentication
    """

    def authenticate(self, username=None, password=None, auto=False, groups_json='myapa/permission_groups.json'):

        user = None

        if getattr(settings, "ENABLE_AUTO_LOGIN", False):
            auto = True

        try:
            # gets username if logging in with email
            if '@' in username:
                user = User.objects.filter(email__iexact=username).first()
            # otherwise if logging in with ID
            else:
                user = User.objects.get(username=username) 
        except:
            return None
        
        if not user:
            # return None in case lookup by email not found
            return None

        if check_password(password, user.password) or auto:
            user.backend = 'django.contrib.auth.backends.ModelBackend' # needed for auth methods to work properly (e.g. login() )
            try:
                # NOTE, failes if node not running...
                # PermissionGroups.update_user_groups(username=user.username, groups_json=groups_json)
                utils.update_user_groups(user)
                Contact.update_or_create_from_imis(user.username)
            except Exception as e:
                print(str(e))
                pass
            user_authenticated = user
        else:
            user_authenticated = None
            
        return user_authenticated


    def get_user(self, username):
        """
        Needed for AuthenticationBackend to work properly
        """
        try:
            return User.objects.select_related("contact").prefetch_related("groups").get(pk=username)

        except User.DoesNotExist:
            return None
