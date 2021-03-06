# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-11-27 22:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imis', '0011_customeventregistration_customeventschedule_eventfunction_namefin_namepicture_namesecurity_orderline'),
    ]

    operations = [
        migrations.CreateModel(
            name='NPC19_Speakers_Temp',
            fields=[
                ('id', models.CharField(db_column='ID', max_length=10, primary_key=True, serialize=False)),
                ('first_name', models.CharField(db_column='First Name', max_length=20)),
                ('last_name', models.CharField(db_column='Last Name', max_length=30)),
                ('email', models.CharField(db_column='Email', max_length=100)),
                ('city', models.CharField(db_column='City', max_length=40)),
                ('state_province', models.CharField(db_column='State', max_length=15)),
                ('zip', models.CharField(db_column='Zipcode', max_length=10)),
                ('pw', models.CharField(db_column='PW', max_length=50)),
            ],
            options={
                'db_table': '_Temp_NPC19_Create_Accounts',
                'managed': False,
            },
        ),
    ]
