# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-12-17 23:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0014_merge_20191017_1313'),
    ]

    operations = [
        migrations.AddField(
            model_name='cadmiummapping',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cadmiummapping',
            name='updated_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='cadmiumsync',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cadmiumsync',
            name='updated_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='microsite',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='microsite',
            name='updated_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='syncmapping',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='syncmapping',
            name='updated_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]