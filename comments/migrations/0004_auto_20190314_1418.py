# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-03-14 19:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0003_auto_20180726_1415'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_type',
            field=models.CharField(choices=[('STORE_REVIEW', 'Product Review'), ('CONTENT', 'General Comments on Content'), ('CM', 'CM Log Comments and Ratings'), ('EVENT_EVAL', 'Event Evaluations'), ('LEARN_COURSE', 'APA Learn Course Eval/Completion'), ('LEARN_SPEAKER', 'APA Learn Speaker Eval/Completion'), ('SPEAKER_EVAL', 'Speaker Evaluations'), ('HIDDEN_LEARN_COURSE', 'Hidden APA Learn Course Eval/Completion')], default='CONTENT', max_length=50),
        ),
    ]
