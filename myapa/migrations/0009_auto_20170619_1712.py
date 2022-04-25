# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-19 22:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapa', '0008_educationaldegree_seqn'),
    ]

    operations = [
        migrations.RenameField(
            model_name='educationaldegree',
            old_name='seqn',
            new_name='school_seqn',
        ),
        migrations.AddField(
            model_name='educationaldegree',
            name='level_other',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]