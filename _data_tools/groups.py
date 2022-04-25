from store.models import *
from myapa.models import *
from django.contrib.auth.models import  Group

def add_pac20_group():
    pwg = Group.objects.get(name="PAC20")
    print("group is ", pwg)
    pac_prod_code = "POL20"
    prod=Product.objects.filter(code=pac_prod_code)
    print("product is ", prod)
    prs = Purchase.objects.filter(product__code=pac_prod_code)
    for pr in prs:
        print("START ----")
        gs = pr.user.groups.all()
        if pwg in gs:
            print("HAS PAC GROUP:")
            print(pr.user.contact)
            print("")
        else:
            print("DID NOT HAVE GROUP, ADDING")
            pwg.user_set.add(pr.user)
        print("")
