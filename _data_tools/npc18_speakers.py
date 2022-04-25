import random
import string
from django.contrib.auth.models import User
from imis.models import *
from myapa.models.contact import Contact
from store.models import Purchase as DjangoPurchase

def create_speakers():
    speakers = NPC18_Speakers_Temp.objects.all()
    errors = []
    for x in speakers:
        try:
            user_id = x.id
            Contact.update_or_create_from_imis(user_id)
            temporary_password = ''.join(random.choice(string.ascii_letters) for x in range(7))
            u = User.objects.get(username=user_id)
            u.set_password(temporary_password)
            u.save()

            x.pw = temporary_password
            x.save()
        except Exception as e:
            errors.append((user_id, str(e)))

    print(str(errors))


def fix_imis_reg_class():
    """
    fixes NPC18 imis reg classes that were originally blank.
    """
    purchases = DjangoPurchase.objects.filter(product__content__master=9135594).exclude(order__isnull=True)
    print("there are {0} purchases that will be updated".format(str(purchases.count())))
    fixed_reg_classes = []
    for x in purchases:
        try:
            imis_reg_class = "" if not x.product_price.imis_reg_class else x.product_price.imis_reg_class
            print("updating user {0} with reg class {1}".format(x.user.username, imis_reg_class))
            imis_invoice_reference_num = Trans.objects.filter(bt_id=x.user.username, product_code__in=["18CONF/M001","18CONF/M002","18CONF/M003","18CONF/M004"]).first().invoice_reference_num
            imis_order_number = Orders.objects.filter(bt_id=x.user.username,invoice_reference_num=imis_invoice_reference_num).first().order_number
            imis_order_meet = OrderMeet.objects.get(order_number=imis_order_number)

            if imis_order_meet.registrant_class == "" or imis_order_meet.registrant_class is None:
                fixed_reg_classes.append({"USER":x.user.username, "Django Order":x.order.id, "Imis Order": imis_order_number})
            imis_order_meet.registrant_class = imis_reg_class
            imis_order_meet.save()
        except Exception as e:
            print("ERROR: " + str(e))
            
    print(str(fixed_reg_classes))

