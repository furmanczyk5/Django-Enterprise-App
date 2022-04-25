import pdfkit

from django.template.loader import render_to_string
from django.views.generic import View
from django.http import HttpResponse

from ui.utils import get_css_path_from_less_path
from myapa.viewmixins import AuthenticateStaffMixin


class PrintPurchasesView(AuthenticateStaffMixin, View):

    is_download = True

    def get(self, request, *args, **kwargs):

        the_css = get_css_path_from_less_path(["/static/content/css/style.less","/static/ui/css/ticket.less"])
        the_html = render_to_string("events/ticket/test.html")
        the_options = {
            "page-size": "Letter",
            "margin-top": "0.5in",
            "margin-right": "0.375in",
            "margin-bottom": "0.375in",
            "margin-left": "0.375in"
        }
        the_pdf = pdfkit.from_string(the_html, False, css=the_css, options=the_options)

        response = HttpResponse(the_pdf, content_type='application/pdf')

        if self.is_download:
            response['Content-Disposition'] = 'attachment; filename="tickets.pdf"'

        return response
