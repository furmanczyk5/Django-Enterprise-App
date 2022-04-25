from myapa.models import IndividualProfile

#  Imports CSV line by line
def import_csv(filename):
    import csv
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            put_statement(row['\ufeffID'], row['Statement'])

# Puts statement from csv into profile for given contact
def put_statement(ID, statement):
    profile = IndividualProfile.objects.get(contact__user__username = ID)
    print (profile.contact)
    profile.statement = statement
    profile.save()

import_csv('_data_tools/2019_AICP_statements.csv')
