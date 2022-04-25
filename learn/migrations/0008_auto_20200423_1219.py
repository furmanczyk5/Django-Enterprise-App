# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-04-23 17:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0024_auto_20200124_1048'),
        ('learn', '0007_auto_20191217_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='learncourseinfo',
            name='activity',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_info_from', to='events.Activity', verbose_name='Activity Pulled From'),
        ),
        migrations.AddField(
            model_name='learncourseinfo',
            name='learncourse',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_info_to', to='learn.LearnCourse', verbose_name='Course Written To'),
        ),
    ]
