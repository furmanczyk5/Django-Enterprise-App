# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2021-06-15 16:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cm', '0014_auto_20201211_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='claim',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
