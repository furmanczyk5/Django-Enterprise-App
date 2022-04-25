# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-22 22:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0003_auto_20181012_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='voter_voice_checksum',
            field=models.CharField(blank=True, help_text='The checksum that is returned by a VoterVoice-validated address', max_length=100, null=True),
        ),
    ]
