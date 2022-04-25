# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-03-06 15:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0021_auto_20190125_1022'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='url',
            field=models.CharField(blank=True, db_index=True, help_text='The url for the content, starting with "/".', max_length=255, null=True),
        ),
    ]
