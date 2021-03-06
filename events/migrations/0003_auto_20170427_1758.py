# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-27 22:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_auto_20170202_1717'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='ticket_template',
            field=models.CharField(blank=True, choices=[('registrations/tickets/layouts/CONFERENCE-BADGE.html', 'NPC Conference Badge'), ('registrations/tickets/layouts/CONFERENCE-ACTIVITY.html', 'NPC Activity Ticket'), ('registrations/tickets/layouts/CONFERENCE-NPC18.html', 'NPC Check out NPC18!'), ('registrations/tickets/layouts/CONFERENCE-FOUNDATION.html', 'NPC Foundation Card'), ('registrations/tickets/layouts/CONFERENCE-SPONSORS.html', 'NPC Sponsor Card'), ('registrations/tickets/layouts/EVENT-MULTI.html', 'Chapter Conference Badge')], max_length=100, null=True, verbose_name='badge/ticket template'),
        ),
    ]
