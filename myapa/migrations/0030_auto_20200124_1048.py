# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-24 16:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapa', '0029_auto_20200122_1618'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contact',
            name='zip_code_extension',
            field=models.CharField(blank=True, help_text='The four-digit ZIP code extension', max_length=4, null=True),
        ),
        migrations.AddField(
            model_name='contactrole',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contactrole',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contactrole',
            name='zip_code_extension',
            field=models.CharField(blank=True, help_text='The four-digit ZIP code extension', max_length=4, null=True),
        ),
    ]