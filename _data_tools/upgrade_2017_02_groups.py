
from django.contrib.auth.models import Permission, User, Group
from content.models import Content
from directories.models import Directory
from store.models import Product, ProductPrice

def get_group_status(group_name=None, group=None, print_status=True, return_dict=False):
    try:
        group = group or Group.objects.get(name=group_name)
        print(group.name)
        status_dict={
            "content__permission_groups": Content.objects.filter(permission_groups=group),
            "product__future_groups": Product.objects.filter(future_groups=group),
            "product_price__required_groups": ProductPrice.objects.filter(required_groups=group),
            "product_price__exclude_groups": ProductPrice.objects.filter(exclude_groups=group),
            "directory__permission_groups": Directory.objects.filter(permission_groups=group),
        }
        status_dict["content__permission_groups__count"] = status_dict["content__permission_groups"].count()
        status_dict["product__future_groups__count"] = status_dict["product__future_groups"].count()
        status_dict["product_price__required_groups__count"] = status_dict["product_price__required_groups"].count()
        status_dict["product_price__exclude_groups__count"] = status_dict["product_price__exclude_groups"].count()
        status_dict["directory__permission_groups__count"] = status_dict["directory__permission_groups"].count()

        if print_status:
            print(status_dict["content__permission_groups__count"], "on Content.permission_groups")
            print(status_dict["product__future_groups__count"], "on Product.future_groups")
            print(status_dict["product_price__required_groups__count"], "on ProductPrice.required_groups")
            print(status_dict["product_price__exclude_groups__count"], "on ProductPrice.exclude_groups")
            print(status_dict["directory__permission_groups__count"], "on Directory.permission_groups")
            must_keep = status_dict["content__permission_groups__count"] +\
                        status_dict["product__future_groups__count"] +\
                        status_dict["product_price__required_groups__count"] +\
                        status_dict["product_price__exclude_groups__count"] +\
                        status_dict["directory__permission_groups__count"]
            if must_keep:
                print("GROUP IS USED: KEEP IT!")
            else:
                print("OK TO DELETE!!!")
        if return_dict:
            return status_dict
    except Group.DoesNotExist:
        print("group does not exist")

def remove_unused_groups():
    pass

def get_groups_mismatched(username):
    pass
