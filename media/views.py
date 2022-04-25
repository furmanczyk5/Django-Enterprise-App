import os
import json

from mimetypes import MimeTypes

from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from .models import Media


class GetMediaHtmlView(View):

    def get(self, request, *args, **kwargs):

        # media_id will be the draft id for people using the admin... TO DO.. should limit the admin to drafts that have been published!
        media_id = kwargs.get("media_id")
        media_draft = Media.objects.filter(id=media_id).select_related("master__content_live__media").first()
        if media_draft.master.content_live:
            media_published = media_draft.master.content_live.media
        return HttpResponse(media_published.to_html())


class GetMediaRssXml(View):

    path_to_xml = "media/podcast.xml"

    def get(self, request, *args, **kwargs):
        return HttpResponse(open(os.path.join(settings.BASE_DIR, self.path_to_xml), encoding="utf-8").read(), content_type='text/xml')


class GetFile(View):
    """
    View for returning a files using a consistent url scheme
        Limited use, currently only for conference mobile app pdf files
    """

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id")
        media = Media.objects.get(master_id=master_id, publish_status="PUBLISHED")
        file = media.get_file()

        mime = MimeTypes()
        mime_type = mime.guess_type(file.url)

        return HttpResponse(file, content_type=mime_type) # May want to put restrictions on this, for now restricting in url routing


class GetFileLastUpdated(View):
    """View for returning json of the last updated time for a media file"""

    def get(self, request, *args, **kwargs):
        master_id = kwargs.get("master_id")
        media = Media.objects.get(master_id=master_id, publish_status="PUBLISHED")
        context = dict(
            success=True,
            id=media.master_id,
            updated_time=media.updated_time # would rather get the actual file metadata, but this is more consistent across systems and file types
        )
        return HttpResponse(json.dumps(context, cls=DjangoJSONEncoder), content_type='application/json')
