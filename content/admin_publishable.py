from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from content.mail import Mail


class AdminPublishableMixin(object):
    """
    Mixin to encapsulate admin publish features all in one spot.
    """
    publishable = True
    show_create_draft = False # True only for submissions...
    show_sync_imis = False # TO DO... this shouldn't be mixed up in publishing. We should deal with iMIS syncing as something completely different.
    show_cm_period_log_drop = False
    post_to_staging_on_save = True
    solr_publishable = True
    show_sync_harvester = False

    def publishable_button_actions(self, request, obj):
        """
        method for dealing with the admin form submission actions for the various save/preview/publish
        buttons....
        """

        # for submissions only... when clicking button to create draft copy from submission
        if "_create_draft" in request.POST:
            obj.publish(publish_type="DRAFT")
            messages.success(request,'Successfully created/updated draft copy for %s' % obj.title)

        # for clicking preview (saves as normal, then redirects to url with querystring that causes a new window to open up
        # with the staging site previw)
        elif "_preview" in request.POST:
            if obj.url:
                return HttpResponseRedirect("%s?publish_status=DRAFT" % obj.url)
            else:
                return HttpResponseRedirect("/%s/%s/%s/?publish_status=DRAFT" % (obj._meta.app_label, obj._meta.model_name, obj.master_id))

        elif "_publish" in request.POST:
            obj.workflow_status = 'IS_PUBLISHED'
            obj.save()

            if obj.content_type == 'KNOWLEDGEBASE_STORY':
                obj.url = '/knowledgebase/story/{}'.format(obj.master_id)
                obj.save()

            if obj.content_type == 'KNOWLEDGEBASE':
                obj.url = '/knowledgebase/resource/{}'.format(obj.master_id)
                obj.save()
           
            self.button_publish(request, obj)

        elif "_send_publish" in request.POST:
            obj.workflow_status = "NEEDS_REVIEW"
            obj.save()

            editor_list = User.objects.filter(groups__name="staff-cms-editor")
            editor_email_list = [a_user.email for a_user in editor_list if a_user.email]
            mail_context = {
                "content": obj,
                "SERVER_ADDRESS": settings.SERVER_ADDRESS
            }
            Mail.send("CMS_CONTENT_NEEDS_REVIEW", editor_email_list, mail_context)



        # TO DO: THIS SHOULD BE REFACTORED AND REMOVED... TO CONFUSING TO MIX UP IMIS SYNC WITH PUBLISHING:
        elif "_sync_imis" in request.POST:
            obj.sync_to_imis()
            messages.success(request,'Successfully posted event %s to iMIS' % obj.title)

    def button_publish(self, request, obj):

        # SAVE CHANGES AND PUBLISHING ALL IN ONE REQUEST DOES NOT SEEM TO WORKING WITH CELERY
        # CELERY IS PUBLISHING OLD RECORDS WHEN IT's TASK IS STARTED BEFORE THE COMPLETION OF THE REQUEST
        # REMOVING SINGLE RECORD ASYNC PUBLISHING FOR THE PUBLISH BUTTON
        # TESTING ASYNC PUBLISHING:
        # obj.publish_async(solr_publish=self.solr_publishable)
        # messages.success(request,'Successfully published... allow a few minutes to see the updates on the website.')

        # comment this back in to disable async publish (but not the except)
        published_obj = obj.publish()
        if self.solr_publishable:
            published_obj.solr_publish()
        messages.success(request, "Successfully published")

    def response_add(self, request, obj):
        return_action = self.publishable_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def response_change(self, request, obj):
        return_action = self.publishable_button_actions(request, obj)
        return_super = super().response_change(request, obj)
        return return_action or return_super

    def publishable_extra_context(self, request, extra_context=None):
        extra_context = extra_context or {}
        has_publish_permission = self.user_has_publish_permission(request)
        extra_context["extra_save_options"] = {
            "show_publish":self.publishable and has_publish_permission,
            "show_send_publish":self.publishable and not has_publish_permission,
            "show_preview":self.publishable,  # for now, let's assume that everything publishable should be able to be previewed
            "show_create_draft":self.show_create_draft,
            "show_sync_imis":self.show_sync_imis and has_publish_permission,  # probably will remove this
            "show_sync_harvester":self.show_sync_harvester,
        }
        return extra_context

    def user_has_publish_permission(self, request):
        """
        Hook so that it is easy to override who has publishing permissions for different types of content
        """
        is_editor = request.user.groups.filter(
            name__in=(
                "staff-editor",
                "staff-events-editor"
            )
        ).exists()
        return is_editor or request.user.is_superuser

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context=self.publishable_extra_context(request, extra_context)
        return super().change_view(request, object_id, form_url,
            extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context=self.publishable_extra_context(request, extra_context)
        return super().add_view(request, form_url='',
            extra_context=extra_context)

    # ---------------------------------------------------------------------------------------------------
    # ---------------------------------------------------------------------------------------------------
    # the following methods are for the mass admin actions (in lower left of admin) for publishing and posting to staging

    def get_actions(self, request):
        """
        built-in django hook that gets the actions for the admin mass action dropdown in lower left... 
        this adds the "post to staging" item and (if the user is an editor) the "publish" item
        """
        actions = super().get_actions(request)
        actions["mass_post_to_staging"] = (self.mass_post_to_staging, "mass_post_to_staging", "Post selected to Staging")

        # get the group names for the admin user... if user is administrator or editor, then can mass publish
        group_names = [g.name for g in request.user.groups.all()]
        if request.user.is_superuser or "staff-editor" in group_names:
            actions["mass_publish"] = (self.mass_publish, "mass_publish", "Publish selected")

        return actions

    def mass_post_to_staging(self, modeladmin, request, queryset):
        """
        Admin action to mass publish content to the staging server and staging solr search.
        """
        try:
            for x in queryset:
                x.publish_async(database_alias="staging", publish_type="DRAFT")
                x.publish_async(database_alias="staging", solr_publish=self.solr_publishable)
        except:
            messages.error(request,"Error posting to staging")

    def mass_publish(self, modeladmin, request, queryset):
        """
        Admin action to call model's publish_to_prod instance method for all selected content,
        Also publishes the content to solr using the Admin action solr_publish
        """
        for x in queryset:
            x.publish_async(solr_publish=self.solr_publishable)

    def mass_solr_publish(modeladmin, request, queryset, solr_base=None, **kwargs):
        """
        To mass add content to solr...
        """
        try:
            queryset.solr_publish(solr_base=solr_base)
            messages.success(request,"Succesfully updated content in search results")
        except:
            messages.error(request, "There was an error updating the records in search results.")

    def mass_solr_unpublish(modeladmin, request, queryset, solr_base=None, **kwargs):
        """
        To mass remove content from solr...
        """
        queryset.solr_unpublish(solr_base=solr_base)
        messages.success(request,'Successfully removed content from search results')
