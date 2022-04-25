from django.contrib.auth.models import Permission, User, Group

import django
django.setup()

COPY_ADMIN_PERMISSIONS_FROM = "136482" # Dorina Blythe

# ADMINS_TO_ADD = ("356121", "125518", "108058", "183959", "346065", "256658")

def add_admin_permissions(*args):
    u_from = User.objects.get(username=COPY_ADMIN_PERMISSIONS_FROM)
    for id in args:
        u = User.objects.get(username=id)
        u.is_staff = True
        u.user_permissions.set(u_from.user_permissions.all())
        u.save()
        print("updated user permissions", u)





# NOTE: something like this could be used in the future to add the above function to migrations
# models.signals.post_migrate.connect(
#     proxy_perm_create)