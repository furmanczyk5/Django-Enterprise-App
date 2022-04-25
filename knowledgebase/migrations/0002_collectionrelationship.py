# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
        ('knowledgebase', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionRelationship',
            fields=[
                ('contentrelationship_ptr', models.OneToOneField(primary_key=True, parent_link=True, serialize=False, auto_created=True, to='content.ContentRelationship')),
            ],
            options={
                'abstract': False,
            },
            bases=('content.contentrelationship',),
        ),
    ]
