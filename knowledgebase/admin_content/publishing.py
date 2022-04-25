def publishing_for_first_time(request, obj):
    return (
        '_publish' in request.POST and
        obj.status == 'A' and
        obj.workflow_status != 'IS_PUBLISHED'
    )


class PublishPermissionMixin(object):
    def user_has_publish_permission(self, request):
        """
        HooK so that it is easy to override who has publishing permissions
        for different types of content
        """
        is_editor = request.user.groups.filter(
            name__in=('staff-editor', 'staff-research')
        ).exists()
        return is_editor or request.user.is_superuser