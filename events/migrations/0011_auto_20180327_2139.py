# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-03-28 02:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_auto_20180322_1445'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventlogentry',
            name='contactcontentadded_ptr',
        ),
        migrations.RemoveField(
            model_name='eventlogentry',
            name='speaker_evals',
        ),
        migrations.RemoveField(
            model_name='speakereval',
            name='contactrole',
        ),
        migrations.RemoveField(
            model_name='speakereval',
            name='event_log_entry',
        ),
        migrations.DeleteModel(
            name='NationalConferenceEval',
        ),
        migrations.DeleteModel(
            name='NationalConferenceProposal',
        ),
        migrations.DeleteModel(
            name='EventLogEntry',
        ),
        migrations.DeleteModel(
            name='SpeakerEval',
        ),
    ]