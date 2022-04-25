# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-07-13 18:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_auto_20180710_0830'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='category',
            field=models.CharField(choices=[('ASC', 'AICP Advanced Specialty Certification (ASC)'), ('CM_SPEAKERS', 'AICP CM Speakers'), ('AICP_CANDIDATE_PROGRAM', 'AICP Candidate Program'), ('AICP', 'AICP Certification Exam'), ('CM', 'AICP Certification Maintenance'), ('FAICP', 'AICP Fellows (FAICP)'), ('FOUNDATION', 'APA Foundation and Scholarships'), ('APA_LEARN', 'APA Learn'), ('LIBRARY', 'APA Library'), ('CAREER', 'Career Services'), ('CPAT', 'Community Planning Assistance (CPAT)'), ('CONSULTANTS_ADVERTISING', 'Consultants/Advertising'), ('ETHICS', 'Ethics'), ('GREAT_PLACES', 'Great Places in America'), ('JOBS', 'Jobs Online/ RFPs and RFQs'), ('MEMBERSHIP', 'Membership'), ('AWARDS', 'National Planning Awards'), ('NPC', 'National Planning Conference'), ('OTHER', 'Other'), ('PAS', 'PAS / Inquiry Answering Service'), ('EARLY_CAREER', 'Student Membership'), ('CONTACT', 'Update MyAPA Info. (email, phone, address)')], max_length=50),
        ),
    ]
