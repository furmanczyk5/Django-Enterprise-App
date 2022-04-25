from wagtail.wagtailcore.models import Page, Site

class ComponentSitesMixin(object):

    page_url = "/"
    extends_template = "component-sites/component-theme/templates/base.html"

    def get_page(self):
        path = self.page_url
        path_components = [component for component in path.split('/') if component]
        page, args, kwargs = self.request.site.root_page.specific.route(self.request, path_components)
        return page

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["extends_template"] = self.extends_template
        context["page"] = self.get_page()
        context["is_wagtail_site"] = True
        return context


# For any component sites view this will get the nav for the appropriate chapter
# expand this to get the footer, etc. also??
# there is also a method version of this because I don't want to have to add this as a mixin 
# on Page models and have to run migrations. So there are two versions. 

# FOR LOGIN WE NEED HTTP BUT FOR OTHER THINGS WE MAY NEED HTTPS -- MAY NEED TO CHANGE:
# rethink this as just for login (and name it as such ?): so it stays just http
class ComponentSitesNavMixin(object):

    def get(self, request,*args,**kwargs):
        host = self.request.META['HTTP_HOST']
        host_no_port = host.split(":")
        site = Site.objects.get(hostname=host_no_port[0])
        self.root_page = Page.objects.get(id=site.root_page_id)
        host_parts = host_no_port[0].split(".")
        main_site = ""
        for part in host_parts:
            if part in ["local-development", "staging", "planning"]:
                main_site = main_site + part + "."
        if len(host_no_port) > 1:
            port = host_no_port[1]
        else:
            port = ""
        main_site = main_site + "org" + ":" + port
        self.http_hostname = "http://" + main_site
        return super().get(request,*args,**kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["page"] = self.root_page
        context["http_hostname"] = self.http_hostname
        context["is_wagtail_site"] = True
        return context
