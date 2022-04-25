# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-24 16:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0005_attendee_voter_voice_checksum'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendee',
            name='longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendee',
            name='zip_code_extension',
            field=models.CharField(blank=True, help_text='The four-digit ZIP code extension', max_length=4, null=True),
        ),
    ]
