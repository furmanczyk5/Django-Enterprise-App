# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-15 19:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    # replaces = [('awards', '0001_initial'), ('awards', '0002_submission_is_finalist'), ('awards', '0003_auto_20150806_1731')]

    initial = True

    dependencies = [
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
        ('submissions', '0001_squashed_0010_auto_20161018_1735'),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='content.Content')),
                ('user_address_num', models.IntegerField(blank=True, null=True)),
                ('address1', models.CharField(blank=True, max_length=40, null=True)),
                ('address2', models.CharField(blank=True, max_length=40, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('is_finalist', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Award Nominations',
                'verbose_name': 'Award Nomination',
            },
            bases=('content.content', models.Model),
        ),
        migrations.CreateModel(
            name='SubmissionCategory',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Award Categories',
                'proxy': True,
                'verbose_name': 'Award Category',
            },
            bases=('submissions.category',),
        ),
        migrations.CreateModel(
            name='JurorAssignment',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name': 'Juror Assignment',
            },
            bases=('submissions.review',),
        ),
    ]
