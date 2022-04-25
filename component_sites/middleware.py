import re

from django.http import Http404


class ComponentSitesMiddleware(object):

    def __init__(self, get_response):
        """
        One-time configuration and initialization for this middleware.
        """
        self.get_response = get_response


    def __call__(self, request):

        # domain = get_current_site(request).domain
        # # NOTE replacing get_current_site call to a read of the host... avoid an additional query?
        host = request.META.get('HTTP_HOST', 'www.planning.org')
        # site = "planning.org" # NOTE: 159.203.164.77 is for

        if host in ["w1", "localhost:8000"]:
            raise Http404

        # environments = "|".join(["local-development", "staging", "www", "159.203.164.77"])
        environments = ["local-development", "staging", "www", "159.203.164.77", "future-www", "192.241.179.148"]
        host_pattern = "(?P<hostname>[^\:]*)(?:\:(?P<port>\d+)|)"
        # site_pattern = "(?:(?P<environment>%s)[\-.,\.]|)(?:(?P<site>(?:.+\.|)planning\.org))" % environments
        site_pattern = "(?:(?P<subdomain>[A-z-]*)\.*)(?:(?P<domain>planning\.org))"

        host_result =  re.match(host_pattern, host)
        host_vars = host_result.groupdict() if host_result else dict()
        hostname = host_vars.get("hostname", "www.planning.org")
        port = host_vars.get("port")

        site_result = re.match(site_pattern, hostname)
        site_vars = site_result.groupdict() if site_result else dict()
        # site = site_vars.get("site", "planning.org")
        # environment = site_vars.get("environment", "www") or "www"
        domain = site_vars.get("domain", "planning.org")
        subdomain = site_vars.get("subdomain", "www")

        # this assumes that the urls will have the format:
        # <component-><environment>.planning.org<:port>
        environment = None
        site = None
        index = -1
        env = next( (e for e in environments if subdomain.find(e) > -1), None)

        if env:
            index = subdomain.find(env)
            environment = env

        # if part of subdomain is in environments list
        if index > -1:
            component_slice_index = 0 if index <= 0 else index - 1
            prod_subdomain = subdomain[0:(component_slice_index)]
            site = prod_subdomain + "." + domain if prod_subdomain else domain

        # if no part of subdomain is in environments list
        if not env:
            site = subdomain + "." + domain if subdomain else domain

        if not environment:
            environment = "www"
        if not site:
            site = "planning.org"

        request.component_site_host = dict(
            hostname=hostname,
            environment=environment,
            planning_home="{protocol}{env}.planning.org{port}".format(
                protocol="http://" if environment == "local-development" else "https://",
                env=environment,
                port=":{port}".format(port=port) if port else ""),
            site=site,
            port=port)

        # TEMP ADD future.planning.org for prod testing
        if site not in ("planning.org", "future.planning.org"):
            request.urlconf = "component_sites.urls"

        return self.get_response(request)
