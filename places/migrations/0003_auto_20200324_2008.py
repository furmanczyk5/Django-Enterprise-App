# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-25 01:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0002_auto_20191217_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentplace',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='places_contentplace_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='places_place_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='place', to='content.Tag'),
        ),
        migrations.AlterField(
            model_name='place',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='places_place_updated_by', to=settings.AUTH_USER_MODEL),
        ),
    ]