# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-10-12 15:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0003_auto_20181002_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
