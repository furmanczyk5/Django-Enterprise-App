# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    	# # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
        ('pages', '0001_squashed_0002_auto_20160601_2348'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='new_landing_page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bak_section', to='pages.LandingPage'),
        ),
        migrations.AddField(
            model_name='content',
            name='parent_landing_master',
            field=models.ForeignKey(blank=True, help_text='The landing page under which this content belongs within the overall sitemap.\n        This determines the side menu (if applicable) and breadcrumb links.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_content', to='pages.LandingPageMasterContent', verbose_name='Parent landing page'),
        ),
        migrations.AddField(
            model_name='menuitem',
            name='parent_landing_page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_menuitems', to='pages.LandingPage'),
        ),
    ]