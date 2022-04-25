# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # ('events', '0020_event_length_in_minutes'),
        # ('events', '0001_squashed_0005_event_ticket_template'),
('events', '0001_squashed_0020_event_length_in_minutes'),
        # ('myapa', '0052_auto_20160401_1543'),
        # ('myapa', '0001_squashed_0007_auto_20161018_1735'),
('myapa', '0001_squashed_0052_auto_20160331_1650'),
        # ('registrations', '0008_auto_20160328_1722'),
        # ('registrations', '0001_squashed_0003_auto_20161019_1514'),
('registrations', '0001_squashed_0008_auto_20160328_1722'),
    ]

    operations = [
        # migrations.CreateModel(
        #     name='ConferenceActivity',
        #     fields=[
        #     ],
        #     options={
        #         'proxy': True,
        #     },
        #     bases=('events.nationalconferenceactivity',),
        # ),
        migrations.CreateModel(
            name='ConferenceAttendee',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('registrations.nationalconferenceattendee',),
        ),
        migrations.CreateModel(
            name='ConferenceContact',
            fields=[
            ],
            options={
                'verbose_name': 'contact',
                'verbose_name_plural': 'lookup contacts',
                'proxy': True,
            },
            bases=('myapa.individualcontact',),
        ),
        # migrations.CreateModel(
        #     name='ConferenceParticipant',
        #     fields=[
        #     ],
        #     options={
        #         'proxy': True,
        #     },
        #     bases=('events.nationalconferenceparticipant',),
        # ),
    ]
