# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-25 03:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imis', '0015_accessmain_addresscategoryref_componentregistry_contactmain_customaicpexamscore_customschoolaccredit'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomAddressGeocode',
            fields=[
                ('id', models.CharField(db_column='ID', max_length=10)),
                ('seqn', models.IntegerField(db_column='SEQN', primary_key=True, serialize=False)),
                ('address_num', models.IntegerField(db_column='ADDRESS_NUM', unique=True)),
                ('votervoice_checksum', models.CharField(blank=True, db_column='VOTERVOICE_CHECKSUM', max_length=255, null=True)),
                ('longitude', models.FloatField(blank=True, db_column='LONGITUDE', null=True)),
                ('latitude', models.FloatField(blank=True, db_column='LATITUDE', null=True)),
                ('weak_coordinates', models.BooleanField(db_column='WEAK_COORDINATES', default=False)),
                ('us_congress', models.CharField(blank=True, db_column='US_CONGRESS', max_length=100, null=True)),
                ('state_senate', models.CharField(blank=True, db_column='STATE_SENATE', max_length=100, null=True)),
                ('state_house', models.CharField(blank=True, db_column='STATE_HOUSE', max_length=100, null=True)),
                ('changed', models.BooleanField(db_column='CHANGED', default=False)),
                ('last_updated', models.DateTimeField(auto_now=True, db_column='LAST_UPDATED')),
            ],
            options={
                'db_table': 'Custom_Address_Geocode',
                'managed': False,
            },
        ),
    ]
