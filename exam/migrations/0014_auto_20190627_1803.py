# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-06-27 23:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0013_auto_20190226_1703'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='code',
            field=models.CharField(blank=True, db_index=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='examapplication',
            name='application_type',
            field=models.CharField(choices=[('REG', 'Regular Applicant'), ('MCIP', 'Canadian Institute of Planners (MCIP)'), ('NJ', 'NJ: applying for AICP only, already passed exam'), ('SCHOLAR', 'SCHOLAR: (archived no longer used) '), ('NJ_REG', 'NJ: applying for AICP and will register for the exam'), ('NJ_NOAICP', 'NJ: Not Applying for AICP – Exam Only'), ('CAND_ENR', 'AICP Candidate Program Enrollment'), ('CAND_CERT', 'AICP Candidate AICP Certification'), ('CAND_RESUB', 'AICP Candidate AICP Certification Resubmission')], max_length=10),
        ),
    ]
