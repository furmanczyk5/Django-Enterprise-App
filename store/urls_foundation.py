from django.conf.urls import url

from store.views import checkout_views

urlpatterns = [

    # FOUNDATION DONATION
    url(r'^waystogive/$', checkout_views.FoundationDonationView.as_view(), name='donation'),
    url(r'^donate/cart/$', checkout_views.FoundationDonationCartView.as_view(), name='donation_cart'),
    url(r"^donors/$", checkout_views.DonorListView.as_view(), name="donor_list"),
    url(r'^donors/onsite/$', checkout_views.OnsiteDonorView.as_view(), name='donors_onsite'),
    url(r'^donors/npc19/$', checkout_views.OnsiteDonorViewSwitcher.as_view()),

    url(
        r'^donation/visualization/$',
        checkout_views.FoundationDonationVisualView.as_view(),
        name='donation_visualization'
    ),

    url(
        r'^donation/visualization/(?P<webpage_type>web)/$',
        checkout_views.FoundationDonationVisualView.as_view(),
        name='donation_visualization_web'
    ),

    url(
        r'^donation/visualization/json/$',
        checkout_views.FoundationDonationVisualJsonDataView2.as_view(),
        name='donation_visualization_json'
    ),

    url(
        r'^donation/visualization/donors/json/$',
        checkout_views.FoundationDonationDonorsJsonDataView.as_view(),
        name='donation_visualization_donors_json'
    )

]
