from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic import View

from content.models import Content


class SubmissionFormDeleteView(View):
    def dispatch(self, request, *args, **kwargs):
        master_id = kwargs.get('master_id', None)
        content = Content.objects.filter(master__id=master_id).first()
        title = content.title

        content.delete()

        messages.success(
            request,
            'Knowledgebase Submission: {0} has been removed'.format(title)
        )
        return HttpResponseRedirect(reverse('knowledgebase:dashboard'))
