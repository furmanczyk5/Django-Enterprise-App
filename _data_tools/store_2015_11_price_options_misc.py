from store.models import ProductPrice

def update_price_options():
    prices = ProductPrice.objects.all()
    for p in prices:
        changed = False
        if p.required_product_option:
            p.option_code = p.required_product_option.code
            changed = True
        if p.required_product:
            p.other_required_product_code = p.required_product.code
            changed = True
            if len(p.required_product_options.all()) > 0:
                p.other_required_option_code = p.required_product_options.all()[0].code
        if changed:
            p.save()


