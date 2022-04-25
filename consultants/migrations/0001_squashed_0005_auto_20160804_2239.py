# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-15 22:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    # replaces = [('consultants', '0001_initial'), ('consultants', '0002_consultantlisting'), ('consultants', '0003_rfp_company'), ('consultants', '0004_branchoffice'), ('consultants', '0005_auto_20160804_2239')]

    initial = True

    dependencies = [
        # ('myapa', '0001_squashed_0007_auto_20161018_1735'),
('myapa', '0001_squashed_0052_auto_20160331_1650'),
        # ('myapa', '0001_squashed_0052_auto_20160331_1650'),
        # ('myapa', '0004_contact_company_fk'),
        # ('myapa', '0002_auto_20160415_1702'),
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='RFP',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='content.Content')),
                ('user_address_num', models.IntegerField(blank=True, null=True)),
                ('address1', models.CharField(blank=True, max_length=40, null=True)),
                ('address2', models.CharField(blank=True, max_length=40, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('rfp_type', models.CharField(choices=[('RFP', 'RFP'), ('RFQ', 'RFQ')], max_length=50, verbose_name='RFP or RFQ')),
                ('deadline', models.DateField(blank=True, null=True)),
                ('email', models.CharField(blank=True, max_length=100, null=True)),
                ('website', models.URLField(blank=True, max_length=255, null=True)),
                ('company', models.CharField(blank=True, max_length=80, null=True)),
            ],
            options={
                'verbose_name_plural': 'RFPs and RFQs',
                'verbose_name': 'RFP or RFQ',
            },
            bases=('content.content', models.Model),
        ),
        migrations.CreateModel(
            name='Consultant',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('myapa.organization',),
        ),
        migrations.CreateModel(
            name='ConsultantListing',
            fields=[
                ('contact_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='myapa.Contact')),
            ],
            options={
                'abstract': False,
            },
            bases=('consultants.consultant',),
        ),
        migrations.CreateModel(
            name='BranchOffice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_address_num', models.IntegerField(blank=True, null=True)),
                ('address1', models.CharField(blank=True, max_length=40, null=True)),
                ('address2', models.CharField(blank=True, max_length=40, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('email', models.CharField(blank=True, max_length=100, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('cell_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('website', models.URLField(blank=True, max_length=255, null=True)),
                ('parent_organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branchoffices', to='consultants.Consultant', verbose_name='main office')),
            ],
            options={
                'verbose_name_plural': 'Branch Offices',
                'verbose_name': 'Branch Office',
            },
        ),
    ]
