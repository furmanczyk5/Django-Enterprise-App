from .db_accessor import DbAccessor
from imis.models import CustomEventRegistration


EMPTY_BADGE = {}
UNITED_STATES = 'United States'
QUERY = (
    'SELECT * FROM Name_Address '
    'INNER JOIN Name '
    'ON Name.id=Name_Address.id '
    "WHERE Name_Address.preferred_mail=1 AND Name.id=?"
)


class Badge():
    def __init__(self):
        self.db = DbAccessor()

    def get(self, id):
        return self.serialize(self.db.get_row(QUERY, id))

    def get_full(self, id):
        row = self.db.get_row(QUERY, id)
        if row:
            return {
                **self.serialize(row),
                **{
                    'first_name': row.FIRST_NAME,
                    'last_name': row.LAST_NAME,
                    'designation': row.DESIGNATION
                }
            }

        return EMPTY_BADGE

    def update(self, id, data):
        CustomEventRegistration.objects.update_or_create(
            id=id,
            defaults=data
        )

    def serialize(self, row):
        if not row:
            return EMPTY_BADGE

        return {
            'badge_name': row.FIRST_NAME,
            'badge_company': row.COMPANY,
            'badge_location': format_location(row),
            'address1': row.ADDRESS_1,
            'address2': row.ADDRESS_2,
            'city': row.CITY,
            'state': row.STATE_PROVINCE,
            'country': row.COUNTRY,
            'zip_code': row.ZIP,
        }


def format_location(row):
    if row.COUNTRY == UNITED_STATES:
        return "{0}, {1}".format(row.CITY, row.STATE_PROVINCE)
    else:
        return "{0}, {1}".format(row.CITY, row.COUNTRY)
