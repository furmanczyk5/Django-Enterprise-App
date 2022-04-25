from django.conf.urls import url

from ui import views

urlpatterns = [

    url(r"^(?P<app>.+)/(?P<model>.+)/autocomplete/$", views.autocomplete),

    url(r"^autocomplete/speaker_formset/$", views.autocomplete, dict(
        app="myapa",
        model="contact",
        record_template="ui/newtheme/autocomplete/record-template/speaker.html")),

    url(r"^autocomplete/attendee_registration/(?P<event_master_id>.+)/$", views.autocomplete, dict(
        app="myapa", 
        model="contact", 
        record_template="ui/newtheme/autocomplete/record-template/attendee-registration.html" )),

    url(r"^autocomplete/add_provider_admin/$", views.autocomplete, dict(
        app="myapa", 
        model="contact", 
        filters=dict(contact_type="INDIVIDUAL"), 
        record_template="ui/newtheme/autocomplete/record-template/add-provider-admin.html" )),
    url(r"^selectable/options/(?P<mode>.+)/$", views.get_selectable_options)
    
]
