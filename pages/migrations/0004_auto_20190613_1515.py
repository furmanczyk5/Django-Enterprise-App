# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-06-13 20:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0003_audiopage_videopage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='landingpage',
            name='sort_field',
            field=models.CharField(blank=True, choices=[('published_time desc', 'Newest to Oldest'), ('published_time asc', 'Oldest to Newest'), ('title asc', 'Title'), ('', 'Relevancy')], default='sort_time desc', max_length=50),
        ),
    ]