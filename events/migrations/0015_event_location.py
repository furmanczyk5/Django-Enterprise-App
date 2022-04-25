# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-06-21 21:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0014_auto_20180607_1447'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='location',
            field=models.TextField(blank=True, help_text='Room or Venue', null=True, verbose_name='Location'),
        ),
    ]