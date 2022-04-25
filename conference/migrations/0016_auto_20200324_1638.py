# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-24 21:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('conference', '0015_auto_20191217_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='microsite',
            name='event_master',
            field=models.ForeignKey(blank=True, help_text='Event associated with microsite', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event_microsite', to='content.MasterContent'),
        ),
        migrations.AlterField(
            model_name='microsite',
            name='home_page',
            field=models.ForeignKey(blank=True, help_text='The page that holds the top bar mega menu nav', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='home_page_microsite', to='pages.LandingPageMasterContent', verbose_name='Microsite home page'),
        ),
        migrations.AlterField(
            model_name='microsite',
            name='search_filters',
            field=models.ForeignKey(blank=True, help_text='The search filters for the microsite', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='microsite', to='content.TagType', verbose_name='Microsite search filters'),
        ),
    ]