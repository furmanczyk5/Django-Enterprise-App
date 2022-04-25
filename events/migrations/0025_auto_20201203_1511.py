# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-12-03 21:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0024_auto_20200124_1048'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='cm_equity_credits',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='cm_targeted_credits',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='cm_targeted_credits_topic',
            field=models.CharField(blank=True, choices=[('SUSTAINABILITY_AND_RESILIENCE', 'Sustainability & Resilience')], max_length=100, null=True),
        ),
    ]
