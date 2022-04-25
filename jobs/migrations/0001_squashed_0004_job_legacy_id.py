# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    # replaces = [('jobs', '0001_initial'), ('jobs', '0002_auto_20160225_0004'), ('jobs', '0003_auto_20160302_0405'), ('jobs', '0004_job_legacy_id')]

    dependencies = [
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('content_ptr', models.OneToOneField(parent_link=True, auto_created=True, serialize=False, to='content.Content', primary_key=True)),
                ('user_address_num', models.IntegerField(null=True, blank=True)),
                ('address1', models.CharField(null=True, blank=True, max_length=40)),
                ('address2', models.CharField(null=True, blank=True, max_length=40)),
                ('city', models.CharField(null=True, blank=True, max_length=40)),
                ('state', models.CharField(null=True, blank=True, max_length=15)),
                ('zip_code', models.CharField(null=True, blank=True, max_length=10)),
                ('country', models.CharField(null=True, blank=True, max_length=20)),
                ('job_type', models.CharField(choices=[('INTERN', 'Internship'), ('ENTRY_LEVEL', 'Entry-level job - 4 weeks online'), ('PROFESSIONAL_2_WEEKS', 'Professional job - 2 weeks online'), ('PROFESSIONAL_4_WEEKS', 'Professional job - 4 weeks online')], default='PROFESSIONAL_4_WEEKS', max_length=50)),
                ('display_contact_info', models.BooleanField(default=False)),
                ('contact_us_first_name', models.CharField(null=True, blank=True, max_length=20)),
                ('contact_us_last_name', models.CharField(null=True, blank=True, max_length=30)),
                ('contact_us_email', models.CharField(null=True, blank=True, max_length=100)),
                ('contact_us_phone', models.CharField(null=True, blank=True, max_length=20)),
                ('company', models.CharField(null=True, blank=True, max_length=80)),
                ('contact_us_address1', models.CharField(null=True, blank=True, max_length=40)),
                ('contact_us_address2', models.CharField(null=True, blank=True, max_length=40)),
                ('contact_us_city', models.CharField(null=True, blank=True, max_length=40)),
                ('contact_us_country', models.CharField(null=True, blank=True, max_length=20)),
                ('contact_us_state', models.CharField(null=True, blank=True, max_length=15)),
                ('contact_us_user_address_num', models.IntegerField(null=True, blank=True)),
                ('contact_us_zip_code', models.CharField(null=True, blank=True, max_length=10)),
                ('salary_range', models.CharField(null=True, blank=True, max_length=50)),
                ('post_time', models.DateTimeField(null=True, blank=True)),
                ('legacy_id', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('content.content', models.Model),
        ),
    ]
