# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-09-21 20:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cm', '0001_squashed_0008_auto_20161122_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='status',
            field=models.CharField(choices=[('A', 'Active'), ('G', 'In Grace Period'), ('R', 'Reinstatement'), ('C', 'Completed and Closed'), ('I', 'Inactive'), ('E_01', 'Exempt - Retired;'), ('E_02', 'Exempt - Unemployed members'), ('E_03', 'Exempt - Planners practicing outside of U.S.'), ('E_06', 'Exempt - Parental leave'), ('E_07', 'Exempt - Military service leave'), ('E_09', 'Exempt - Health leave'), ('E_10', 'Exempt - Care leave'), ('E_11', 'Exempt - Foreign residency'), ('E_12', 'Exempt - Other (case-by-case)'), ('E_13', 'Exempt - Voluntary Life option'), ('D', 'Dropped'), ('RA', 'Reinstatement Amnesty')], default='A', max_length=50),
        ),
    ]
