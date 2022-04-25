from django import template

from content.models import Content
from myapa.models import IndividualProfile
from places.models import PlaceData


register = template.Library()


display_statuses = {
    'N': 'Incomplete',
    'P': 'Under Review',
    'A': 'Published',
	'I': 'Not Accepted',
	'CA': 'Removed',
}


display_review_statuses = {
    'REVIEW_RECEIVED': 'Under Review',
    'REVIEW_UNDERWAY': 'Under Review',
    'REVIEW_COMPLETE_ADDED': 'Published',
    'REVIEW_COMPLETE_DUPLICATIVE': 'Not Accepted',
    'REVIEW_COMPLETE_OFF_TOPIC': 'Not Accepted',
}


EMPTY_STRING = ''


@register.filter
def get_place_name(place):
    descriptor = getattr(place, 'place_descriptor_name', None)
    title = getattr(place, 'title', None)
    state_code = getattr(place, 'state_code', None)

    if descriptor == 'state' and title:
        return title

    if title and state_code:
        return '{}, {}'.format(title, state_code)
    
    return EMPTY_STRING


@register.filter
def get_place_data(place):
    return PlaceData.objects.filter(place_id=place.id)


@register.filter
def get_population_data(place):
    data = PlaceData.objects.filter(place_id=place.id).first()
    population = getattr(data, 'population', None)

    if population:
        return '{:,}'.format(population)

    return EMPTY_STRING


@register.filter
def get_population_density(place):
    data = PlaceData.objects.filter(place_id=place.id).first()
    density = data.get_density

    if density:
        return "{:,.2f}".format(data.get_density())
    
    return EMPTY_STRING


@register.filter
def get_collections(content):
    collections = content.related.all()
    collection_titles = []
    for collection in collections:
        live_title = collection.content_live.title
        draft_title = collection.content_draft.title
        if live_title:
            collection_titles.append(live_title)
        else:
            collection_titles.append(draft_title)

    return ', '.join(sorted(collection_titles))


@register.filter
def format_authors_without_links(contact_roles):
    names = []
    for role in contact_roles:
        display_name = _get_display_name(role)
        if display_name:
            names.append(display_name)

    return ', '.join(sorted(names))


@register.filter
def format_author_with_link(role):
    contact = role.contact
    contact_id = contact.id
    profile = IndividualProfile.objects.filter(contact_id=contact_id).first()
    display_name = _get_display_name(role)
    if profile and profile.share_profile != 'PRIVATE' and profile.slug:
        return '<a href="/profile/{}">{}</a>'.format(profile.slug, display_name)
    else:
        return display_name


@register.filter
def get_display_status(status):
    return '<span>{}</span>'.format(display_statuses[status])


@register.filter
def get_display_review_status(review_status):
    return '<span>{}</span>'.format(display_review_statuses[review_status])


def _get_display_name(role):
    display_name = getattr(role.contact, 'title', None)
    first_name = getattr(role.contact, 'first_name', None)
    last_name = getattr(role.contact, 'last_name', None)

    if first_name and last_name:
        display_name = '{} {}'.format(first_name, last_name)

    if not display_name and role.role_type == 'PUBLISHER':
        display_name = getattr(role, 'company', None)

    return display_name
