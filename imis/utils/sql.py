"""sql.py

Tools for creating raw SQL queries for use in iMIS.
These are particularly needed when trying to write data to iMIS (INSERT/UPDATE)
due to certain limitations in our iMIS setup and the Django ORM.

Many tables in iMIS have compound primary keys and no individually unique column.
In this case, our Django model definitions will have no field with `primary_key=True` defined.
When that happens, Django assumes you already have a primary key field called id and tries to
include it in any transaction that writes/updates data in this model. Since these tables do not
have any field called id, it will raise an Exception.

Other tables have a field called id that is not unique but part of a compound primary key
(the Subscriptions table is a prominent example). If the id field exists but is not unique
it seems that Django will just silently overwrite the one existing record in the database
with that id, even if the table was clearly designed to have multiple values in the id
field as part of a compound primary key.

So far, the only two options to seemingly remedy this are to add unique primary key columns to
all affected iMIS tables or drop down to raw SQL when writing to iMIS from Django.
Currently the latter approach seems to be eaiser.

NOTE: This means we need take extreme care to avoid opening ourselves up to SQL injection attacks.
NEVER use standard string formatting to build up queries; ALWAYS use the `params` keyword argument
in the `cursor.execute` statement.

https://docs.djangoproject.com/en/1.11/topics/security/#sql-injection-protection
"""

import datetime
from collections import namedtuple

from django.db import connections

from imis import models as imis_models

# The key in the DATABASES dictionary in planning.settings.local that points to iMIS
IMIS_DB_NAME = 'MSSQL'


def format_values(data):
    """
    Process data by type for building up a raw SQL INSERT query in iMIS
    :param data: dict
    :return: dict
    """
    formatted_data = dict()
    for key, value in data.items():
        if isinstance(value, datetime.datetime):
            formatted_data[key] = value.strftime('%Y-%m-%d %H:%M:%S.000')
        elif isinstance(value, datetime.date):
            formatted_data[key] = value.strftime('%Y-%m-%d 00:00:00.000')
        elif isinstance(value, bool):
            if value:
                formatted_data[key] = 1
            else:
                formatted_data[key] = 0
        else:
            formatted_data[key] = value
    if '_state' in formatted_data:
        formatted_data.pop('_state')
    return formatted_data


def has_id_field(data):
    """
    Does this data dictionary have a field called id or ID?
    :param data: dict
    :return: tuple (bool, key)
    """
    if 'ID' in data:
        return True, 'ID'
    if 'id' in data:
        return True, 'id'
    return False, None


def make_insert_statement(table_name, data, exclude_id_field=True):
    """
    Build up a INSERT statement for iMIS tables with the compound primary key/no id column
    issue described above
    :param table_name: str, the Table name
    :param data: dict, the {column name: value} to insert into the table
    :param exclude_id_field: bool, whether or not to include "id" in the SELECT Statement

    :return:
    """
    ins = "INSERT INTO {} (".format(table_name)
    id_field = has_id_field(data)
    if id_field[0] and exclude_id_field:
        data.pop(id_field[1])
    for key in data.keys():
        ins += "{}, ".format(key.upper())
    ins = ins[:-2] + ") VALUES ("
    ins += '%s, ' * len(data)
    ins = ins[:-2] + ')'
    return ins


def make_select_statement(imis_model_name, exclude_id_field=True):
    """
    Build up a SELECT statement for iMIS tables with all fields represented.
    SELECT * FROM has some quirks...
    :param imis_model_name: str, the class name in :mod:`imis.models` to select from
    :param exclude_id_field: bool, whether or not to include "id" in the SELECT Statement
    :return: str

    TODO: make this an imis model mixin
    """
    model = getattr(imis_models, imis_model_name)
    select = "SELECT "
    for field in model._meta.fields:
        if field.name.upper() == "ID" and exclude_id_field:
            continue
        select += "{}, ".format(field.name.upper())
    select = select[:-2] + " FROM {}".format(model._meta.db_table)
    return select


def make_select_statement_no_model(table_name, fields, exclude_id_field=True):
    """
    Variation of make_select_statement for when you aboslutely, positively
    have to completely bypass the Django ORM.
    :param table_name: str, the iMIS table name
    :param fields: list, of field names
    :param exclude_id_field: bool, whether or not to include "id" in the SELECT Statement
    :return: str
    """
    select = "SELECT "
    for field in fields:
        if field.upper() == "ID" and exclude_id_field:
            continue
        select += "{}, ".format(field.upper())
    select = select[:-2] + " FROM {}".format(table_name)
    return select


def do_insert(insert_statement, data):
    """
    Make the DB API cursor call to execute the INSERT statement
    :param insert_statement: str, return value of `.make_insert_statement`
    :param data: dict, return value of `.format_values`
    :return: None
    """
    with connections[IMIS_DB_NAME].cursor() as cursor:
        cursor.execute(insert_statement, list(data.values()))


def do_select(select_statement, params=None):
    """
    Make the DB API cursor call to execute the SELECT statement
    :param select_statement: str
    :param params: list, params to pass in to (e.g. in a WHERE clause)
    :return: `.namedtuplefetchall`
    """
    with connections[IMIS_DB_NAME].cursor() as cursor:
        cursor.execute(select_statement, params)
        return cursor.fetchall()


def namedtuplefetchall(cursor):
    """
    Return all rows from a cursor as a namedtuple
    :param cursor: :class:`django.db.backends.utils.CursorDebugWrapper`
    :return: list
    """
    desc = cursor.description
    nt_result = namedtuple('ImisResult', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
