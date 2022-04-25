# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    # replaces = [('imagebank', '0001_initial'), ('imagebank', '0002_image_image_file'), ('imagebank', '0003_auto_20150715_2032'), ('imagebank', '0004_remove_image_image_file_size'), ('imagebank', '0005_image_keywords'), ('imagebank', '0006_remove_image_keywords')]

    dependencies = [
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('content_ptr', models.OneToOneField(primary_key=True, auto_created=True, to='content.Content', parent_link=True, serialize=False)),
                ('resolution', models.IntegerField(verbose_name='DPI', blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('image_file', models.ImageField(upload_to='imagebank', height_field='height', width_field='width', blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('content.content',),
        ),
    ]
