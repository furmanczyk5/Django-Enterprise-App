# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-09-21 21:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exam', '0008_auto_20170921_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='examapplication',
            name='application_type',
            field=models.CharField(choices=[('REG', 'Regular Applicant'), ('MCIP', 'Canadian Institute of Planners (MCIP)'), ('NJ', 'NJ: applying for AICP only, already passed exam'), ('SCHOLAR', 'SCHOLAR: (archived no longer used) '), ('NJ_REG', 'NJ: applying for AICP and will register for the exam'), ('NJ_NOAICP', 'NJ: Not Applying for AICP – Exam Only'), ('CEP', 'AICP Certified Environmental Planner'), ('CTP', 'AICP Certified Transportation Planner'), ('CUD', 'AICP Certified Urban Designer'), ('CAND_ENR', 'AICP Candidate Program Enrollment'), ('CAND_CERT', 'AICP Candidate AICP Certification'), ('CAND_RESUB', 'AICP Candidate AICP Certification Resubmission')], max_length=10),
        ),
        migrations.AlterField(
            model_name='examregistration',
            name='registration_type',
            field=models.CharField(choices=[('CEP_A', 'CEP_A: AICP CEP'), ('CEP_T_0', 'CEP_T_0: AICP CEP Transfer from previos - no fee'), ('CEP_T_100', 'CEP_T_100: AICP CEP Transfer from previos - $150 fee'), ('CTP_A', 'CTP_A: AICP CTP'), ('CTP_T_0', 'CTP_T_0: AICP CTP Transfer from previos - no fee'), ('CTP_T_100', 'CTP_T_100: AICP CTP Transfer from previos - $150 fee'), ('CUD_A', 'CUD_A: AICP CUD'), ('CUD_T_0', 'CUD_T_0: AICP CUD Transfer from previous - no fee'), ('CUD_T_100', 'CUD_T_100: AICP CUD Transfer from previous - $150 fee'), ('MCIP_A', 'MCIP_A: Canadian Institute of Planners (MCIP)'), ('NJ_NOAICP', 'NJ_NOAICP: NJ: registering for exam, not applying for AICP'), ('NJ_REG_A', 'NJ_REG_A: registering and applied for AICP'), ('REG_A', 'REG_A: Regular Applicant - Pre Approved'), ('REG_T_0', 'REG_T_0: Transfer from previous-no fee'), ('REG_T_100', 'REG_T_100: Transfer from previous-150$ fee'), ('SCHOLAR_A', 'SCHOLAR_A: Scholarship Recipient'), ('PDO', 'PDO: Professional Development Officer registration'), ('CAND_ENR_A', 'AICP Candidate - $100'), ('CAND_T_0', 'AICP Candidate Free Transfer - $0'), ('CAND_T_100', 'AICP Candidate Transfer - $100')], max_length=20),
        ),
    ]