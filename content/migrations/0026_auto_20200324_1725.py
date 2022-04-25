# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-24 22:25
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
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_content_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='content',
            name='show_content_without_groups',
            field=models.BooleanField(default=False, help_text='\n        Enable if content should be displayed (e.g. as marketing material), even if the user does not have the required permission groups.\n        Generally used for media/resources where the media download may be restricted to certain groups, but we always want to show\n        the content text for marketing purposes.\n        '),
        ),
        migrations.AlterField(
            model_name='contentrelationship',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_contentrelationship_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='contenttagtype',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_contenttagtype_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_menuitem_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='messagetext',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_messagetext_published_by', to=settings.AUTH_USER_MODEL),
        ),
    ]