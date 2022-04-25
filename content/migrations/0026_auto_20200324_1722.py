# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-24 22:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0025_auto_20191217_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_content_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='content',
            name='featured_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='featured_image_content', to='media.MediaImageMasterContent'),
        ),
        migrations.AlterField(
            model_name='content',
            name='master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content', to='content.MasterContent'),
        ),
        migrations.AlterField(
            model_name='content',
            name='og_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='og_image_content', to='media.MediaImageMasterContent'),
        ),
        migrations.AlterField(
            model_name='content',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='content.MasterContent'),
        ),
        migrations.AlterField(
            model_name='content',
            name='parent_landing_master',
            field=models.ForeignKey(blank=True, help_text='The landing page under which this content belongs within the overall sitemap.\n        This determines the side menu (if applicable) and breadcrumb links.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sub_content', to='pages.LandingPageMasterContent', verbose_name='Parent landing page'),
        ),
        migrations.AlterField(
            model_name='content',
            name='serial_pub',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='content.SerialPub'),
        ),
        migrations.AlterField(
            model_name='content',
            name='show_content_without_groups',
            field=models.BooleanField(default=False, help_text='\n        Enable if content should be displayed (e.g. as marketing material), even if the user does not have the required permission groups.\n        Generally used for media/resources where the media download may be restricted to certain groups, but we always want to show\n        the content text for marketing purposes.\n        '),
        ),
        migrations.AlterField(
            model_name='content',
            name='submission_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content', to='submissions.Category'),
        ),
        migrations.AlterField(
            model_name='content',
            name='submission_period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content', to='submissions.Period'),
        ),
        migrations.AlterField(
            model_name='content',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_content_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_emailtemplate_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_emailtemplate_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='mastercontent',
            name='content_draft',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_draft', to='content.Content'),
        ),
        migrations.AlterField(
            model_name='mastercontent',
            name='content_live',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_live', to='content.Content'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_menuitem_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='content.MasterContent', verbose_name='Associated Content'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='submenuitems', to='content.MenuItem', verbose_name='parent menu item'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='parent_landing_page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_menuitems', to='pages.LandingPage'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_menuitem_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='messagetext',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_messagetext_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='messagetext',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_messagetext_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='serialpub',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_serialpub_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='serialpub',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_serialpub_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tag',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_tag_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tag',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='content.Tag'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_tag_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tagtype',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_tagtype_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tagtype',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='content.TagType'),
        ),
        migrations.AlterField(
            model_name='tagtype',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='content_tagtype_updated_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
