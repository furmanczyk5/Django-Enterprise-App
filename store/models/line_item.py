from django.db import models
from django.contrib.auth.models import User

from content.models import BaseContent, BaseAddress
from myapa.models.contact import Contact

# TO DO: consider removing BaseAddress (shipping address fields)
# since we no longer ship any products...
class LineItem(BaseContent, BaseAddress):
    """
    represents a line item for an order. address attributes represent shipping address
    for purchases (where applicable), and billing address for payments
    """
    # NOTE.. in general ALL line items require a user...
    # however we still need to keep historical data around even if user records merged/deleted, so making this optional
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    contact = models.ForeignKey(Contact, null=True, blank=True, editable=False, on_delete=models.SET_NULL) # eventually, we'll tie purchases to contacts instead of users

    order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.SET_NULL) # (line items with null orders are still in the cart / not submitted)
    gl_account = models.CharField(max_length=50)
    amount = models.DecimalField(decimal_places=2, max_digits=9) # total $ amount for the line item
    submitted_time = models.DateTimeField(null=True, blank=True)

    imis_trans_line_number = models.IntegerField(null=True, blank=True)
    legacy_id = models.IntegerField(null=True, blank=True)
    imis_trans_number = models.IntegerField(null=True, blank=True)
    imis_batch = models.CharField(max_length=50, null=True, blank=True)
    imis_batch_date = models.DateField(null=True, blank=True)


    def __init__(self, *args, **kwargs):
        self._meta.get_field('status').default = "P"
        super(LineItem, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True
