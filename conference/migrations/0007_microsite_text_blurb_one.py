# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-10-16 21:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0006_auto_20181218_1342'),
    ]

    operations = [
        migrations.AddField(
            model_name='microsite',
            name='text_blurb_one',
            field=models.TextField(blank=True, null=True, verbose_name='All purpose text blurb number one'),
        ),
    ]