# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    	('content', '0002_pages_dependency'),
        ('media', '0001_squashed_0004_auto_20160105_2018'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='featured_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='featured_image_content', to='media.MediaImageMasterContent'),
        ),
    ]
