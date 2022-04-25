# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        # ('content', '0049_auto_20160113_2323'),
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('content.content',),
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'All resources',
            },
            bases=('content.content',),
        ),
        migrations.CreateModel(
            name='HealthResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('knowledgebase.resource',),
        ),
        migrations.CreateModel(
            name='SolarResource',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('knowledgebase.resource',),
        ),
    ]
