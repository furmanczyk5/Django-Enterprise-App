# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-05-21 19:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0022_auto_20190125_1012'),
        ('learn', '0004_auto_20180814_1707'),
    ]

    operations = [
        migrations.CreateModel(
            name='LearnCourseInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('run_time', models.DurationField(blank=True, null=True)),
                ('run_time_cm', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('vimeo_id', models.IntegerField(blank=True, null=True)),
                ('lms_course_id', models.CharField(blank=True, db_index=True, max_length=200, null=True)),
                ('lms_template', models.IntegerField(blank=True, null=True)),
                ('lms_product_page_url', models.URLField(blank=True, max_length=255, null=True)),
                ('activity_from', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activity_to_info', to='events.Activity')),
                ('course_to', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_from_info', to='learn.LearnCourse')),
            ],
        ),
    ]
