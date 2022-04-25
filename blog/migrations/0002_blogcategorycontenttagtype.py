# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # ('content', '0065_auto_20160401_1553'),
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogCategoryContentTagType',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'blog categories',
                'verbose_name': 'blog category',
            },
            bases=('content.contenttagtype',),
        ),
    ]
