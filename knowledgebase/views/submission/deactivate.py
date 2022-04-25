from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic import View

from content.models import Content, MasterContent


class SubmissionFormDeactivateView(View):
    def dispatch(self, request, *args, **kwargs):
        master_id = kwargs.get('master_id', None)
        all_versions = Content.objects.filter(master__id=master_id)

        if all_versions and all_versions[0].status == 'N':
            self.delete(master_id, all_versions)
        else:
            self.deactivate(all_versions)

        messages.success(
            request,
            'Knowledgebase Submission: {0} has been removed'.format(master_id)
        )
        return HttpResponseRedirect(reverse('knowledgebase:dashboard'))

    def delete(self, master_id, content_results):
        master = MasterContent.objects.get(id=master_id)
        for content in content_results:
            content.delete()
        master.delete()

    def deactivate(self, content_results):
        for content in content_results:
            content.status = 'CA'
            content.save()
