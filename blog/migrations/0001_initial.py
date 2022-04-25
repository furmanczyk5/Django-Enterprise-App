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
            name='BlogPost',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('content.content',),
        ),
    ]
