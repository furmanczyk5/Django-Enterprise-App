# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2021-06-28 20:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_auto_20201203_1511'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='cm_ethics_requested',
        ),
        migrations.RemoveField(
            model_name='event',
            name='cm_law_requested',
        ),
        migrations.RemoveField(
            model_name='event',
            name='cm_requested',
        ),
        migrations.AlterField(
            model_name='event',
            name='cm_approved',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='cm_equity_credits',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='cm_ethics_approved',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='cm_law_approved',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='cm_targeted_credits',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
        ),
    ]