# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-22 22:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('free_students', '0005_auto_20191217_1711'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='voter_voice_checksum',
            field=models.CharField(blank=True, help_text='The checksum that is returned by a VoterVoice-validated address', max_length=100, null=True),
        ),
    ]