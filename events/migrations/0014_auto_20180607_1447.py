# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-06-07 19:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0013_auto_20180606_1157'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='learning_objectives',
            field=models.TextField(blank=True, null=True, verbose_name='Learning Objectives'),
        ),
        migrations.AddField(
            model_name='event',
            name='more_details',
            field=models.TextField(blank=True, null=True, verbose_name='More Details'),
        ),
    ]
