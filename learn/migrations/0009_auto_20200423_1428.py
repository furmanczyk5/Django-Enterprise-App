# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-04-23 19:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learn', '0008_auto_20200423_1219'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learncourseinfo',
            name='activity_from',
        ),
        migrations.RemoveField(
            model_name='learncourseinfo',
            name='course_to',
        ),
    ]
