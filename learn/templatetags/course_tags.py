from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def all_price_options(context):
    """
    Get all pricing options with ProductOption titles
    :param context: template context
    :return: dict
    """
    # TO DO: this should be refactored based on 2018-11 store / price refactoring

    all_options = []
    if not context.get('product_prices'):
        return []
    for price in context['product_prices']:
        if price.status != 'A':
            continue
        option_title = ''
        sort_number = 1
        option_id = None
        # TODO: There should be a better way of getting the ProductOption title
        # that doesn't involve re-querying.
        # Maybe use a select_related query in RenderContent.set_product?
        options = price.product.options.filter(code=price.option_code, status__in=('A', 'H'))
        is_user_price = False
        if options.exists():
            option_title = options.first().title
            sort_number = options.first().sort_number
            option_id = options.first().id
            is_user_price = price.product.get_price(contact=context['contact'], option=options.first()) == price
        all_options.append(
            dict(
                option_title=option_title,
                option_id=option_id,
                title=price.title,
                price=price.price,
                sort_number=sort_number,
                status=price.status,
                min_quantity=price.min_quantity,
                max_quantity=price.max_quantity,
                is_user_price=is_user_price
            )
        )
    return sorted(all_options, key=lambda x: x['sort_number'])
