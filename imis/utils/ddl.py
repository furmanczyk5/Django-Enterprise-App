from django.db import connections
from imis import models as imis_models
import os


conn = connections['MSSQL']

IMIS_MODELS = [
    'Activity',
    'Advocacy',
    'Counter',
    'CustomDegree',
    'CustomEventRegistration',
    'CustomEventSchedule',
    'CustomSchoolaccredited',
    'EventFunction',
    'IndDemographics',
    'MailingDemographics',
    'MeetMaster',
    'MeetResources',
    'NPC18_Speakers_Temp',
    'NPC19_Speakers_Temp',
    'Name',
    'NameAddress',
    'NameFin',
    'NamePicture',
    'NameSecurity',
    'OrderLines',
    'OrderMeet',
    'Orders',
    'OrgDemographics',
    'Product',
    'ProductFunction',
    'ProductInventory',
    'ProductPrice',
    'RaceOrigin',
    'Relationship',
    'ScoresDemographics',
    'Subscriptions',
    'Trans',
    'ZipCode'
]

MSSQL_POSTGRES_DTYPES = {
    'bit': 'boolean',
    'datetime2': 'timestamp',
}


def make_create_table(table_name):
    stmnt = "CREATE TABLE {} (".format(table_name)
    return stmnt


def create_field(field):
    stmnt = "{name} {dtype}".format(**field)
    if not field['null']:
        stmnt += " NOT NULL"
    if field['primary_key']:
        stmnt += " PRIMARY KEY"
    stmnt += ', '
    return stmnt


def gen_schema():
    with open('/Users/cmollet/Documents/imis/schema.sql', 'w') as sqlfile:
        for name in IMIS_MODELS:
            model = getattr(imis_models, name)
            sql = make_create_table(model._meta.db_table)
            for field in model._meta.fields:
                data = get_field_data(field)
                sql += create_field(data)
            sql = sql[:-2] + ');'
            sqlfile.write(sql)
            sqlfile.write('\n')

def get_field_dtype(dtype):
    if dtype == 'nvarchar(max)':
        return 'text'
    elif dtype.startswith('nvarchar'):
        return dtype.replace('nvarchar', 'varchar')
    elif dtype.startswith('int'):
        return 'int'
    else:
        if dtype in MSSQL_POSTGRES_DTYPES:
            return MSSQL_POSTGRES_DTYPES[dtype]
        else:
            return dtype


def get_field_data(field):
    return dict(
        primary_key=field.primary_key,
        null=field.null,
        dtype=get_field_dtype(field.db_type(conn)),
        name=field.name,
        max_length=field.max_length,
        blank=field.blank,
        index=field.db_index,
        default=field.default
    )


