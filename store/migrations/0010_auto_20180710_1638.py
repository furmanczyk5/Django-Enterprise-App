# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-07-10 21:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_auto_20180710_1109'),
    ]

    operations = [
        migrations.AddField(
            model_name='productprice',
            name='max_quantity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='productprice',
            name='min_quantity',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
