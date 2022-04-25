# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import media.models


class Migration(migrations.Migration):

    # replaces = [('media', '0001_initial'), ('media', '0002_auto_20151221_1702'), ('media', '0003_mediaimagemastercontent'), ('media', '0004_auto_20160105_2018')]

    dependencies = [
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('content_ptr', models.OneToOneField(serialize=False, parent_link=True, primary_key=True, to='content.Content', auto_created=True)),
                ('media_format', models.CharField(max_length=20, default='DOCUMENT', choices=[('DOCUMENT', 'Document'), ('IMAGE', 'Image'), ('VIDEO', 'Video'), ('AUDIO', 'Audio')])),
                ('url_source', models.CharField(max_length=20, default='NA', choices=[('NA', 'Not Applicable'), ('YOUTUBE', 'Youtube Video'), ('SOUNDCLOUD', 'Soundcloud Audio'), ('STITCHER', 'Stitcher')])),
                ('file_type', models.CharField(max_length=20, default='NA', choices=[('NA', 'Not Applicable'), ('JPG', 'Jpg')])),
                ('resolution', models.IntegerField(blank=True, verbose_name='DPI', null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('width', models.IntegerField(blank=True, null=True)),
                ('image_file', models.ImageField(height_field='height', upload_to=media.models.Media.generate_file_path, blank=True, null=True, width_field='width')),
                ('uploaded_file', models.FileField(upload_to=media.models.Media.generate_file_path, blank=True, null=True)),
            ],
            options={
                # 'abstract': False,
                'verbose_name_plural': 'All Media',
            },
            bases=('content.content',),
        ),
        migrations.CreateModel(
            name='Audio',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('media.media',),
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('media.media',),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('media.media',),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('media.media',),
        ),
        # migrations.AlterModelOptions(
        #     name='media',
        #     options={'verbose_name_plural': 'All Media'},
        # ),
        migrations.CreateModel(
            name='MediaImageMasterContent',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('content.mastercontent',),
        ),
        # migrations.AlterField(
        #     model_name='media',
        #     name='url_source',
        #     field=models.CharField(max_length=20, default='NA', choices=[('NA', 'Not Applicable'), ('YOUTUBE', 'Youtube Video'), ('SOUNDCLOUD', 'Soundcloud Audio'), ('STITCHER', 'Stitcher')]),
        # ),
    ]
