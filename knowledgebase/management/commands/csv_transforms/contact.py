# used in other modules that import * from here
from functools import reduce


PREFIX_NAMES = [
    'Adm.', 'Admiral',
    'Gen.', 'General',
    'Dr.', 'Doctor',
    'Mrs.', 'Missus', 'Missis', 'Misses',
    'Ms.', 'Miss',
    'Mr.', 'Mister',
    'Rev.', 'Reverend',
    'Hon.', 'Honorable'
]


def add_contact(row_dict):
    author = row_dict.pop('Author').strip()
    if author:
        row_dict['contact'] = transform_contact(author)

    return row_dict


def transform_contact(author):
    if is_author(author):
        contact = {
            'contact_type': 'INDIVIDUAL'
        }
        name = clean_name(author)
        last_name, first_name = name.rsplit(',', 1)
        handle_last_name(last_name, contact)
        handle_first_name(first_name, contact)
        add_default_null_fields(contact)
        return contact

    return {
        'company': author,
        'contact_type': 'ORGANIZATION'
    }


def is_author(author):
    return ',' in author


def clean_name(author):
    return (
        ' '.join(author.split())
            .strip()
            .replace(' , ', ',')
            .replace(' .', '.')
    )


def handle_last_name(last_name, contact):
    if includes_suffix_name(last_name):
        last_name, suffix_name = last_name.rsplit(',', 1)
        contact['suffix_name'] = suffix_name.strip()
        
    contact['last_name'] = last_name

    return contact


def includes_suffix_name(last_name):
    return ',' in last_name


def handle_first_name(first_name, contact):
    split_name = first_name.split()
    prefix = get_prefix(first_name)

    if is_single_name(split_name):
        contact['first_name'] = first_name
    elif prefix:
        split_name = split_prefixed_name(first_name, prefix)
        contact['prefix_name'] = split_name[0]
        handle_first_name(split_name[1], contact)
    elif has_middle_name(split_name):
        contact['first_name'] = split_name[0]
        contact['middle_name'] = split_name[1]
    # Some authors have 3 names for a first name, like Russell Van Nest
    elif len(split_name) > 2:
        contact['first_name'] = split_name[0]
        contact['middle_name'] = ' '.join(split_name[1:])

    return contact


def is_single_name(split_name):
    return len(split_name) == 1


def contains_prefix_name(first_name):
    for prefix in PREFIX_NAMES:
        if prefix in first_name:
            return True
    
    return False


def get_prefix(first_name):
    for prefix in PREFIX_NAMES:
        if prefix in first_name:
            return prefix


def split_prefixed_name(first_name, prefix):
    partition = list(first_name.partition(prefix))
    first_name = partition.pop().strip()
    return [''.join(partition).strip(), first_name]


def has_middle_name(split_name):
    return len(split_name) == 2


def add_default_null_fields(contact):
    contact['email'] = None
    contact['member_type'] = None
    contact['city'] = None
    contact['state'] = None
    return contact
