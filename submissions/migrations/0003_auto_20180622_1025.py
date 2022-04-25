# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-06-22 15:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0002_auto_20180131_1559'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='review_status',
            field=models.CharField(choices=[('REVIEW_RECEIVED', 'Review Recieved'), ('REVIEW_UNDERWAY', 'Review Underway'), ('REVIEW_COMPLETE_ACCEPTED', 'Review Completed: ACCEPTED'), ('REVIEW_COMPLETE_DUPLICATIVE', 'Review Completed: DUPLICATIVE'), ('REVIEW_COMPLETE_OFF_TOPIC', 'Review Completed: OFF-TOPIC')], default='REVIEW_RECEIVED', max_length=50),
        ),
        migrations.AlterField(
            model_name='category',
            name='content_type',
            field=models.CharField(choices=[('PAGE', 'Web page'), ('EVENT', 'Events & training'), ('RFP', 'RFP/RFQ'), ('KNOWLEDGEBASE', 'Planning knowledgebase entry'), ('KNOWLEDGEBASE_COLLECTION', 'Planning knowledgebase collection'), ('KNOWLEDGEBASE_STORY', 'Planning knowledgebase collection'), ('KNOWLEDGEBASE_SUGGESTION', 'Planning knowledgebase collection'), ('AWARD', 'Award nomination'), ('RESEARCH_INQUIRY', 'Research inquiry'), ('IMAGE', 'Image library image'), ('MEDIA', 'Media asset'), ('PRODUCT', 'Other product'), ('PUBLICATION', 'Publication (article or resource)'), ('BLOG', 'Blog post'), ('EXAM', 'Exam application submission'), ('JOB', 'Job ad')], default='PAGE', max_length=50),
        ),
        migrations.AlterField(
            model_name='period',
            name='content_type',
            field=models.CharField(choices=[('PAGE', 'Web page'), ('EVENT', 'Events & training'), ('RFP', 'RFP/RFQ'), ('KNOWLEDGEBASE', 'Planning knowledgebase entry'), ('KNOWLEDGEBASE_COLLECTION', 'Planning knowledgebase collection'), ('KNOWLEDGEBASE_STORY', 'Planning knowledgebase collection'), ('KNOWLEDGEBASE_SUGGESTION', 'Planning knowledgebase collection'), ('AWARD', 'Award nomination'), ('RESEARCH_INQUIRY', 'Research inquiry'), ('IMAGE', 'Image library image'), ('MEDIA', 'Media asset'), ('PRODUCT', 'Other product'), ('PUBLICATION', 'Publication (article or resource)'), ('BLOG', 'Blog post'), ('EXAM', 'Exam application submission'), ('JOB', 'Job ad')], default='AWARDS', max_length=50),
        ),
        migrations.AlterField(
            model_name='review',
            name='review_type',
            field=models.CharField(choices=[('AWARDS_JURY', 'Awards Jury'), ('RESEARCH_INQUIRY', 'PAS Research Inquiry'), ('EXAM_REVIEW', 'Exam Application Reviewer'), ('CONFERENCE_PROPOSAL_REVIEW', 'Conference Proposal Review'), ('KNOWLEDGEBASE_SUGGESTION_REVIEW', 'Knowledgebase Suggestion Review'), ('KNOWLEDGEBASE_STORY_REVIEW', 'Knowledgebase Story Review')], default='AWARDS_JURY', max_length=50),
        ),
        migrations.AlterField(
            model_name='reviewrole',
            name='review_type',
            field=models.CharField(choices=[('AWARDS_JURY', 'Awards Jury'), ('RESEARCH_INQUIRY', 'PAS Research Inquiry'), ('EXAM_REVIEW', 'Exam Application Reviewer'), ('CONFERENCE_PROPOSAL_REVIEW', 'Conference Proposal Review'), ('KNOWLEDGEBASE_SUGGESTION_REVIEW', 'Knowledgebase Suggestion Review'), ('KNOWLEDGEBASE_STORY_REVIEW', 'Knowledgebase Story Review')], default='AWARDS_JURY', max_length=50),
        ),
    ]
