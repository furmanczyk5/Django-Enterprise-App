import sys

from django.contrib.auth.management import _get_all_permissions
from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.apps import apps
from django.utils.encoding import smart_text
from django.db import models

import django
django.setup()

from content.models import *

# THERE IS A BUG IN DJANGO WITH PROXY MODEL PERMISSIONS (see: https://code.djangoproject.com/ticket/11154 )
# RUN THIS TO FIX PERMISSIONS FOR PROXY MODELS (from https://gist.github.com/magopian/7543724 )
def proxy_perm_create(**kwargs):
    for model in apps.get_models():
        opts = model._meta
        ctype, created = DjangoContentType.objects.get_or_create(
            app_label=opts.app_label,
            model=opts.object_name.lower(),
            # defaults={'name': smart_text(opts.verbose_name_raw)}
            )
        if created:
            print(ctype)

        for codename, name in _get_all_permissions(opts):
            p, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=ctype,
                defaults={'name': name})
            if created:
                sys.stdout.write('Adding permission {}\n'.format(p)
                    )


# Created for new proxy models to create perm for all subclassed models.
# Just import the model and send it to the function below.
def singular_proxy_perm_create(pmodel):
    opts = pmodel._meta
    ctype, created = DjangoContentType.objects.get_or_create(
        app_label=opts.app_label,
        model=opts.object_name.lower(),
        # defaults={'name': smart_text(opts.verbose_name_raw)}
        )
    if created:
        print(ctype)

    for codename, name in _get_all_permissions(opts):
        p, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=ctype,
            defaults={'name': name})
        if created:
            sys.stdout.write('Adding permission {}\n'.format(p)
                )


def update_page_areas(**kwargs):
    Content.objects.filter(content_type="PAGE", content_area="RESEARCH").update(content_area="KNOWLEDGE_CENTER")
    Content.objects.filter(content_type="PAGE", content_area="DIVISIONS").update(content_area="CONNECT")
    Content.objects.filter(content_type="PAGE", content_area="CHAPTERS").update(content_area="CONNECT")

def assign_perm(app_label=None, model=None, can_whats=(), group_names=(), ctype=None):
    try:
        ctype = ctype or DjangoContentType.objects.get(app_label=app_label, model=model)
        model = model or ctype.model
        for can_what in can_whats:
            try:
                permission = Permission.objects.get(content_type=ctype, codename=can_what + "_" + model)
                for group_name in group_names:
                    try:
                        group = Group.objects.get(name=group_name)
                        group.permissions.add(permission)
                        print("added %s %s" % (group_name, can_what + "_" + model))
                    except Group.DoesNotExist:
                        print("ERROR: could not load group: %s " % group_name)
            except Permission.DoesNotExist:
                print("ERROR: could not get permission record for: %s | %s" % (ctype, can_what + "_" + model))
    except DjangoContentType.DoesNotExist:
        print("ERROR: could not load content type: %s %s " % (ctype, model) )



def assign_app_perm(app_label, can_whats, group_names):
    for ctype in DjangoContentType.objects.filter(app_label=app_label):
        assign_perm(ctype=ctype, can_whats=can_whats, group_names=group_names)

def mass_update_perms():

    for group in Group.objects.all():
        group.permissions.clear()

    assign_perm("pages", "landingpage",
        ("change","add"),
        ("staff-editor",) ) # QUESTION: should marketing be able to add landing page?

    assign_perm("pages", "membershippage",
        ("change","add"),
        ("staff-editor","staff-marketing","staff-membership") )

    assign_perm("pages", "knowledgecenterpage",
        ("change","add"),
        ("staff-editor","staff-education","staff-marketing","staff-publications","staff-research","staff-careers","staff-communications") )

    assign_perm("pages", "conferencespage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-conference","staff-policy","staff-aicp","staff-research") )

    assign_perm("pages", "aicppage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-aicp") )

    assign_perm("pages", "policypage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-policy","staff-communications") )

    assign_perm("pages", "policypage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-policy","staff-communications") )

    assign_perm("pages", "careerpage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-careers","staff-leadership") )

    assign_perm("pages", "outreachpage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-policy","staff-communications","staff-aicp","staff-leadership","staff-education") )

    assign_perm("pages", "connectpage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-leadership","staff-aicp") )

    assign_perm("pages", "aboutpage",
        ("change","add"),
        ("staff-editor", "staff-marketing","staff-leadership","staff-communications") )

    assign_perm("content", "contentrelationship",
        ("change","add","delete"),
        ("staff",) )

    assign_perm("pages", "landingpagemastercontent",
        ("change",),
        ("staff",) )

    assign_perm("content", "jurisdictioncontenttagtype",
        ("change","add"),
        ("staff",) )

    assign_perm("content", "communitytypecontenttagtype",
        ("change","add"),
        ("staff",) )

    assign_perm("content", "formatcontenttagtype",
        ("change","add"),
        ("staff",) )

    assign_perm("content", "taxotopictag",
        ("change","add"),
        ("staff",) )

    assign_perm("content", "contenttagtype",
        ("change","add"),
        ("staff",) )

    assign_perm("content", "content",
        ("change",),
        ("staff",) )

    assign_app_perm("publications",
        ("change","add"),
        ("staff-editor","staff-marketing","staff-publications","staff-communications") )

    assign_app_perm("blog",
        ("change","add"),
        ("staff",) )

    assign_app_perm("knowledgebase",
        ("change","add"),
        ("staff-editor","staff-research") )

    assign_app_perm("research_inquiries",
        ("change","add"),
        ("staff-editor","staff-research") )

    assign_app_perm("submissions",
        ("change","add"),
        ("staff-editor",) )

    assign_app_perm("awards",
        ("change","add"),
        ("staff-editor", "staff-policy", "staff-communications") )

    assign_app_perm("jobs",
        ("change","add"),
        ("staff-editor",) )

    assign_app_perm("exam",
        ("change","add"),
        ("staff-aicp", "staff-membership") )

    assign_app_perm("content",
        ("change","add"),
        ("staff-editor",) )

    assign_app_perm("myapa",
        ("change","add"),
        ("staff",) )

    assign_perm("myapa", "individual",
        ("change"),
        ("onsite-conference-admin",))

    assign_app_perm("support",
        ("change","add"),
        ("staff",) )

    assign_app_perm("store",
        ("change","add"),
        ("staff-editor", "staff-store-admin") )

    assign_app_perm("events",
        ("change","add"),
        ("staff-editor", "staff-store-admin","staff-education","staff-conference", "staff-policy", "staff-careers", "staff-aicp") )

    assign_app_perm("registrations",
        ("change","add"),
        ("staff-editor", "staff-store-admin","staff-education","staff-conference","staff-aicp","onsite-conference-admin") )

    assign_app_perm("consultants",
        ("change","add"),
        ("staff-editor", "staff-conference") )

    assign_app_perm("directories",
        ("change","add"),
        ("staff-editor", "staff-leadership") )

    assign_app_perm("media",
        ("change","add"),
        ("staff",) )

    assign_app_perm("imagebank",
        ("change","add"),
        ("staff",) )

    assign_app_perm("cm",
        ("change","add"),
        ("staff-aicp", "staff-membership") )

    assign_app_perm("learn",
        ("change","add"),
        ("staff-education", "staff-editor", "staff-store-admin", "staff-membership", "staff-aicp") )

    assign_app_perm("places",
        ("change","add"),
        ("staff-research",) )

    assign_perm("auth", "user",
        ("change",),
        ("staff","onsite-conference-admin") )

    assign_perm("redirects", "redirect",
        ("change","add","delete"),
        ("staff-editor",) )

    assign_perm("conference", "microsite",
        ("change", "add"),
        ("staff-editor",) )

def remove_superuser(**kwargs):
    User.objects.filter(is_superuser=True).update(is_superuser=False)
    User.objects.filter(username__in=("143742","275301","261337","297075","322218","315520")).update(is_superuser=True)


def add_tagging_to_research():
    """Give the staff-research group taxo topic/jurisdiction/etc. tagging perms"""
    assign_perm("content", "taxotopictag",
                ("change", "add"),
                ("staff-research",))

    assign_perm("content", "jurisdictioncontenttagtype",
                ("change", "add"),
                ("staff-research",))

    assign_perm("content", "communitytypecontenttagtype",
                ("change", "add"),
                ("staff-research",))

    assign_perm("content", "formatcontenttagtype",
                ("change", "add"),
                ("staff-research",))

    assign_perm("content", "contenttagtype",
                ("change", "add"),
                ("staff-research",))

    assign_perm("content", "content",
                ("change",),
                ("staff-research",))

# NOTE: something like this could be used in the future to add the above function to migrations
# models.signals.post_migrate.connect(
#     proxy_perm_create)
