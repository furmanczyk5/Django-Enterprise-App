


p = Product.objects.filter(
    status__in=("A","H")).select_related("content").prefetch_related(
        models.Prefetch("prices", 
            queryset=ProductPrice.objects.order_by("priority").prefetch_related("exclude_groups", "required_groups")
            )
    )
