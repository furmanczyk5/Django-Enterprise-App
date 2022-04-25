from django.conf.urls import include, url

urlpatterns = [

    # mobile app api
    url(r"^api/(?P<version>0\.(0|1|2|3))/", include("conference.urls.api", namespace="mobileapp_api")),
    # Use this regex to match any version (?P<version>\d+(\.\d+)*)

    # onsite registration kiosk
    url(r"^kiosk/", include("conference.urls.kiosk", namespace="npc_kiosk")),
    url(r"^(?P<master_id>\d+)/kiosk/", include("conference.urls.kiosk", namespace="kiosk")),

    # online conference program
    url(r"^", include("conference.urls.program", namespace="program")),

    # harvester sync
    url(r"^harvester/", include("conference.urls.harvester", namespace="harvester")),

    # every conference microsite url will be prefixed with conference/<conference_id>/
    url(r"^(?P<conference_name>\S+?)/", include("conference.urls.microsites", namespace="microsites")),

]
