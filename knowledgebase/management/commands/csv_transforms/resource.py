REMAINDER_TEXT = (
    ', an electronic text contained in the APA Library E-book Collection. '
    'This text is available to APA members as a benefit of membership.'
)

ELLIPSE = '...'


def remove_author(row_dict):
    row_dict.pop('Author')
    return row_dict


def remove_year(row_dict):
    row_dict.pop('Year')
    return row_dict


def add_resource_url(row_dict):
    row_dict['resource_url'] = row_dict.pop('Link')
    return row_dict


def add_title(row_dict):
    page = row_dict['Starting Page'].strip()
    title = row_dict.pop('Title')

    if page:
        page = ' (p. {})'.format(page)
        if len(title) + len(page) > 200:
            title = trim_title(title, ELLIPSE, page)
        else:
            title = '{}{}'.format(title, page)
    else:
        if len(title) > 200:
            title = trim_title(title, ELLIPSE)

    row_dict['title'] = title
    return row_dict

      
def trim_title(title, ellipse, page=''):
    if len(title) + len(ellipse) + len(page) > 200:
        split_title = title.split()
        split_title.pop()
        return trim_title(' '.join(split_title), ellipse, page)
    
    return '{}{}{}'.format(title, ellipse, page)


def add_subtitle(row_dict):
    row_dict['subtitle'] = row_dict.pop('Volume')
    return row_dict


def add_text(row_dict):
    volume = row_dict.get('Volume')
    if not volume:
        volume = row_dict.get('subtitle')
    page = row_dict.pop('Starting Page')
    row_dict['text'] = text_formatter(volume, page)
    row_dict['description'] = row_dict['text']
    return row_dict


def text_formatter(volume, page):
    if page:
        location_text = 'This resource is on page %s of %s' %(page, volume,)
    else:
        location_text = 'This resource is available in %s' %(volume,)

    return location_text + REMAINDER_TEXT


def add_additional_data(row_dict):
    row_dict['status'] = 'A'
    row_dict['publish_status'] = 'DRAFT'
    row_dict['workflow_status'] = 'DRAFT_IN_PROGRESS'
    return row_dict