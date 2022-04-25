from django.conf.urls import url
from django.views.generic import TemplateView

from registrations.views import registration_redirect
from store.views import checkout_views, admin_views
from .views import CartView

urlpatterns = [

    # TO DO... THESE URLS ARE LEGACY AND AHOULD BE DELETED
    url(r'^registration/(?P<event_id>[0-9]+)/$', registration_redirect, name='registration_old'),


    url(r'^cart/$', CartView.as_view(),
        name='cart'),

    url(r'^checkout/$', checkout_views.CheckoutView.as_view(),
        name='checkout'),

    url(r'^checkout/done/$', checkout_views.CheckoutDoneView.as_view(),
        name='checkout_done'),

    url(r'^order_confirmation/$', checkout_views.OrderDetailView.as_view(),
        name='order_confirmation'),
    url(r'^order_confirmation/(?P<order_id>[0-9]+)/$', checkout_views.OrderDetailView.as_view(),
        name='order_confirmation'),

    url(r'^payment_callback/$', checkout_views.PaymentCallbackVeiw.as_view(),
        name='payment_callback'),

    url(r'^manage/(?P<order_id>[0-9]+)/payment/cc/$', admin_views.manage_payment_cc,),
    url(r'^manage/(?P<order_id>[0-9]+)/payment/none/$', admin_views.submit_none_payment,),
    url(r'^manage/(?P<order_id>[0-9]+)/payment/refund/$', admin_views.submit_payment_refund,),
    url(r'^manage/(?P<order_id>[0-9]+)/comp-tickets/update/$', admin_views.update_comp_tickets,),

    url(r'^manage/(?P<order_id>[0-9]+)/(?P<product_id>[0-9]+)/(?P<option_id>\w+)/get_price/$', admin_views.get_price,),

    url(r'^include/cart/$', TemplateView.as_view(template_name="store/newtheme/includes/cart-from-user.html"), kwargs={"remove_is_form":True} ),
    url(r'^cart/add/$', checkout_views.AddToCartView.as_view(), name="cart_add" ),
    url(r'^cart/remove/$', checkout_views.RemoveFromCartView.as_view(), name="cart_remove" ),
    url(r'^cart/add/(?P<return_type>json)/$', checkout_views.AddToCartView.as_view() ),
    url(r'^cart/update/(?P<return_type>json)/$', checkout_views.UpdateCartView.as_view() ),
    url(r'^cart/remove/(?P<return_type>json)/$', checkout_views.RemoveFromCartView.as_view() ),


    # move this to a new views file?
    # FOR STORE REDIRECT:
    url(r'^product/$', checkout_views.product_redirect ),

    url(r'^admin/order/(?P<order_id>[0-9]+)/email-confirmation/$', admin_views.OrderConfirmationAdminEmailView.as_view(),
        name='admin_order_confirmation'),
    url(r'^admin/order/(?P<order_id>\d+)/provider-submit/$', admin_views.CMOrderProviderSubmitView.as_view(),
        name='admin_order_provider_submit'),

    url(
        r'^bluepay/return/(?P<username>[0-9]+)/(?P<bill_frequency>[0-9]{1,2})/(?P<bill_period>[0-9]{1,2})/$',
        checkout_views.BluepayReturnView.as_view(), name='bluepay_return'
    )
]
