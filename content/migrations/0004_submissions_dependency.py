# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_media_dependency'),
        ('submissions', '0001_squashed_0010_auto_20161018_1735'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='submission_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='content', to='submissions.Category'),
        ),
        migrations.AddField(
            model_name='content',
            name='submission_period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='content', to='submissions.Period'),
        ),
    ]

