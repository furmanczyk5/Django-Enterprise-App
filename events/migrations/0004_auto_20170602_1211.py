# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-02 17:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20170427_1758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('EVENT_MULTI', 'Multipart Event'), ('EVENT_SINGLE', 'Single Event'), ('ACTIVITY', 'Activity'), ('COURSE', 'On Demand'), ('EVENT_INFO', 'Informational Event')], default='EVENT_SINGLE', max_length=50),
        ),
    ]
