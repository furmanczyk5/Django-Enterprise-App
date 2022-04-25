# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-21 19:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapa', '0009_auto_20170619_1712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationaldegree',
            name='level',
            field=models.CharField(choices=[('B', 'Undergraduate'), ('M', 'Graduate'), ('P', 'PhD/J.D.'), ('N', 'Other Degree')], max_length=50),
        ),
    ]