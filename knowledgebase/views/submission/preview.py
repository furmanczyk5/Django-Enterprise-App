from django.views.generic import TemplateView

from content.models import Content
from myapa.viewmixins import AuthenticateMemberMixin


class SubmissionPreviewView(AuthenticateMemberMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get('master_id')
        self.content = Content.objects.filter(
            master_id=master_id, publish_status='DRAFT'
        ).first()

        self.collection_titles = self.get_collection_titles()

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content'] = self.content
        context['collection_titles'] = self.collection_titles
        return context

    def get_collection_titles(self):
        collection_titles = []

        for collection in self.content.related.all():
            live_title = collection.content_live.title
            draft_title = collection.content_draft.title
            if live_title:
                collection_titles.append(live_title)
            else:
                collection_titles.append(draft_title)

        return ', '.join(sorted(collection_titles))


class StoryPreviewView(SubmissionPreviewView):
    template_name = 'knowledgebase/newtheme/story-details.html'


class ResourcePreviewView(SubmissionPreviewView):
    template_name = 'knowledgebase/newtheme/resource-details.html'
