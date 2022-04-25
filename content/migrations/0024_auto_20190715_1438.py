# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-07-15 19:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0023_auto_20190307_1439'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tag',
            options={'ordering': ['title']},
        ),
        migrations.AlterField(
            model_name='content',
            name='template',
            field=models.CharField(blank=True, choices=[('pages/newtheme/default.html', 'Default web page'), ('cm/newtheme/aicp-page-sidebar.html', 'AICP branded page with sidebar'), ('blog/newtheme/post.html', 'Blog Post'), ('store/newtheme/foundation/page-sidenav.html', 'Foundation branded page with sidebar'), ('knowledgebase/newtheme/collection.html', 'Knowledgebase collection template'), ('knowledgebase/newtheme/resource.html', 'Knowledgebase resource template'), ('knowledgebase/newtheme/story.html', 'Knowledgebase story template'), ('events/newtheme/eventmulti-details.html', 'Multipart event template'), ('events/newtheme/ondemand/course-details.html', 'On-demand template'), ('learn/newtheme/course-details.html', 'APA Learn course template'), ('publications/newtheme/planning-mag.html', 'Planning Magazine article'), ('store/newtheme/product/details.html', 'Product template'), ('publications/newtheme/publication-document.html', 'Publication document template'), ('pages/newtheme/research.html', 'Research project'), ('pages/newtheme/section-overview.html', 'Section overview page'), ('events/newtheme/event-details.html', 'Single event or activity template'), ('pages/newtheme/landing.html', 'Topic landing page'), ('pages/newtheme/full-width.html', 'Full Width (no side nav)'), ('newtheme/templates/conference/page-ads.html', 'Conference (Original Page Template)'), ('newtheme/templates/conference/page-widget.html', 'Conference Page WITH Sidebar AND WIDGET'), ('newtheme/templates/conference/page-sidebar.html', 'Conference Page WITH Sidebar (general)'), ('newtheme/templates/conference/page-nosidebar.html', 'Conference Page WITHOUT Sidebar'), ('events/newtheme/conference-details.html', 'Conference Activity Details'), ('conference/newtheme/home.html', 'Conference Home'), ('pages/micro/home.html', 'Micro home page'), ('pages/micro/default.html', 'Micro default page'), ('pages/micro/section-overview.html', 'Micro section overview page'), ('pages/micro/landing.html', 'Micro topic landing page'), ('pages/micro/home/default.html', 'Home default page'), ('pages/micro/home/section-overview.html', 'Home section overview page'), ('pages/micro/home/landing.html', 'Home topic landing page'), ('pages/newtheme/media.html', 'Media Page')], max_length=50, null=True),
        ),
    ]
