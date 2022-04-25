# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-12-14 22:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapa', '0022_auto_20181127_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='staff_teams',
            field=models.TextField(blank=True, help_text='Department/team names for APA staff for granting django admin access. \n        Staff may belong to multiple teams if they perform cross-departmental work that requires\n        access to specific apps or pages. Enter values in CAPS, \n        separated by commas WITH NO SPACES. Possible values: \n        AICP,\n        CAREERS,\n        COMMUNICATIONS,\n        COMPONENT_ADMIN,\n        COMPONENT_BLACK,\n        COMPONENT_CITY,\n        COMPONENT_HOUSING,\n        COMPONENT_PRIVATE,\n        COMPONENT_TRANS,\n        COMPONENT_URBAN_DES,\n        COMPONENT_WOMEN,\n        CONFERENCE,\n        EDITOR,\n        EDUCATION,\n        EVENTS_EDITOR,\n        KNOWLEDGEBASE_EDITOR,\n        LEADERSHIP,\n        MARKETING,\n        MEMBERSHIP,   \n        PUBLICATIONS,\n        RESEARCH,\n        STORE_ADMIN,\n        TEMP_STAFF\n        ', null=True),
        ),
    ]