# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-30 20:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0011_auto_20180327_2139'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='mail_badge',
            field=models.BooleanField(default=True),
        ),
    ]
