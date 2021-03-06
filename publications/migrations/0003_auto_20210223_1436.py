# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2021-02-23 20:36
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0002_auto_20180131_1559'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Book',
        ),
        migrations.DeleteModel(
            name='EBook',
        ),
        migrations.AlterModelOptions(
            name='publication',
            options={'verbose_name': 'Publication', 'verbose_name_plural': 'All publications'},
        ),
        migrations.AlterField(
            model_name='multipleformatsrelated',
            name='code',
            field=models.CharField(blank=True, db_index=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='multipleformatsrelated',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publications_multipleformatsrelated_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='multipleformatsrelated',
            name='status',
            field=models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], db_index=True, default='A', max_length=5, verbose_name='visibility status'),
        ),
        migrations.AlterField(
            model_name='multipleformatsrelated',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='publications_multipleformatsrelated_updated_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
