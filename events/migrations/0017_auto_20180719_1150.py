# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-07-19 16:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0016_auto_20180710_1109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('EVENT_MULTI', 'Multipart Event'), ('EVENT_SINGLE', 'Single Event'), ('ACTIVITY', 'Activity'), ('COURSE', 'On Demand'), ('EVENT_INFO', 'Informational Event'), ('LEARN_COURSE', 'APA Learn Course'), ('LEARN_COURSE_BUNDLE', 'APA Learn Course Bundle')], default='EVENT_SINGLE', max_length=50),
        ),
    ]