# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-09-06 19:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapa', '0017_individualprofile_speaker_opt_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='individualprofile',
            name='experience',
            field=models.TextField(blank=True, help_text='ASC Experience', null=True),
        ),
    ]