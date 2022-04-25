from django.conf.urls import url

from conference.views import kiosk as views

urlpatterns = [

    url(r'^$', views.KioskHomeLoginView.as_view(), name="home"),
    url(r'^select_action/$', views.KioskSelectActionView.as_view(), name="select_action"),
    url(r'^registration-options/$', views.KioskSelectRegistrationOptionView.as_view(), name="registration_options" ),
    url(r'^badge/$', views.KioskCustomizeBadgeView.as_view(), name="edit_badge"),
    url(r'^add-activities/$', views.KioskAddActivitiesView.as_view(), name="add_activities" ),
    url(r'^cart/$', views.KioskCartView.as_view(), name="cart" ),
    url(r'^checkout/$', views.KioskCheckoutView.as_view(), name="checkout" ),
    url(r'^order-confirmation/(?P<order_id>\d+)/$', views.KioskOrderConfirmation.as_view(), name="order_confirmation"),
    url(r'^reprint/$', views.KioskReprintView.as_view(), name="reprint" ),
    url(r'^foundation/donation/cart/$', views.KioskFoundationDonationCartView.as_view(), name='foundation_donation_cart'),
    
    # technically not kiosk, these urls are for screens used onsite:
    url(r'^available-tickets-screen/$', views.TicketsAvailablePreviewView.as_view(), name="tickets-available-screen"),
    url(r'^upnext-screen/$', views.upnext_screen, name="upnext-screen"),
    
]
