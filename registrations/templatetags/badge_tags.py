from django import template

register = template.Library()


MEMBER = 'MEM'
STUDENT = 'STU'
FULL_MEMBER_TYPE = {
    MEMBER: 'MEMBER',
    STUDENT: 'STUDENT'
}


@register.filter
def get_full_name(badge):
    first_name = badge.get('first_name', '')
    last_name = badge.get('last_name', '')
    designation = badge.get('designation', '')
    full_name = ''

    if first_name and last_name:
        full_name = '{} {}'.format(badge['first_name'], badge['last_name'])

    if designation and full_name:
        full_name += ', {}'.format(designation)

    return full_name


@register.simple_tag
def get_display_member_type(badge):
    member_type = badge.get('member_type', '')

    if member_type.upper() in [MEMBER, STUDENT]:
        return FULL_MEMBER_TYPE[member_type]

    return ''
