# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-16 19:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    # replaces = [('exam', '0001_squashed_0006_auto_20160318_1936'), ('exam', '0002_auto_20160428_2211'), ('exam', '0003_auto_20160503_1543'), ('exam', '0004_auto_20160518_2228'), ('exam', '0005_auto_20160601_2336'), ('exam', '0006_auto_20160607_1740'), ('exam', '0007_auto_20160616_2022'), ('exam', '0008_examapplication_current_review_round'), ('exam', '0009_auto_20161018_1735'), ('exam', '0010_auto_20161103_1055'), ('exam', '0011_examregistration_is_pass')]

    initial = True

    dependencies = [
        ('submissions', '0001_squashed_0010_auto_20161018_1735'),
        # ('store', '0001_squashed_0007_auto_20161018_1734'),
('store', '0001_squashed_0041_auto_20160312_0447'),
        # ('uploads', '0001_squashed_0003_auto_20161018_1735'),
('uploads', '0001_squashed_0012_auto_20160212_2132'),
        # ('submissions', '0008_review_custom_text_2'),
        # ('myapa', '0001_squashed_0007_auto_20161018_1735'),
('myapa', '0001_squashed_0052_auto_20160331_1650'),
        # ('submissions', '0001_squashed_0028_auto_20160401_1553'),
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationDegree',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('other_school', models.CharField(blank=True, max_length=80, null=True)),
                ('graduation_date', models.DateField(blank=True, null=True)),
                ('level', models.CharField(choices=[('B', 'Undergraduate'), ('M', 'Graduate'), ('P', 'PhD/J.D.'), ('O', 'Other Degree')], max_length=50)),
                ('is_planning', models.BooleanField(default=False)),
                ('pab_accredited', models.BooleanField(default=False)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapa.IndividualContact')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='application_degree', to='myapa.School')),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('publish_status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('SUBMISSION', 'Submission'), ('EARLY_RESUBMISSION', 'Early Resubmission')], default='DRAFT', max_length=50)),
                ('publish_time', models.DateTimeField(blank=True, null=True, verbose_name='publish time')),
                ('publish_uuid', models.CharField(blank=True, default=uuid.uuid4, max_length=36, null=True)),
                ('published_time', models.DateTimeField(blank=True, editable=False, null=True)),
            ],
            options={
                'abstract': False,
                'permissions': (('can_publish', 'Can publish'),),
            },
        ),
        migrations.CreateModel(
            name='ApplicationJobHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('company', models.CharField(blank=True, max_length=80, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('is_current', models.BooleanField(default=True)),
                ('is_part_time', models.BooleanField(default=False)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapa.IndividualContact')),
                ('supervisor_name', models.CharField(blank=True, max_length=30, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('is_planning', models.BooleanField(default=False)),
                ('contact_employer', models.BooleanField(default=False)),
                ('publish_status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('SUBMISSION', 'Submission'), ('EARLY_RESUBMISSION', 'Early Resubmission')], default='DRAFT', max_length=50)),
                ('publish_time', models.DateTimeField(blank=True, null=True, verbose_name='publish time')),
                ('publish_uuid', models.CharField(blank=True, default=uuid.uuid4, max_length=36, null=True)),
                ('published_time', models.DateTimeField(blank=True, editable=False, null=True)),
            ],
            options={
                'abstract': False,
                'permissions': (('can_publish', 'Can publish'),),
            },
        ),
        migrations.CreateModel(
            name='VerificationDocument',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('uploads.documentupload',),
        ),
        migrations.AddField(
            model_name='applicationjobhistory',
            name='verification_document',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='exam.VerificationDocument'),
        ),
        migrations.AddField(
            model_name='applicationdegree',
            name='verification_document',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='exam.VerificationDocument'),
        ),
        # migrations.AlterField(
        #     model_name='applicationdegree',
        #     name='level',
        #     field=models.CharField(choices=[('B', 'Undergraduate'), ('M', 'Graduate'), ('P', 'PhD/J.D.'), ('O', 'Other Degree')], max_length=50),
        # ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=200, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status')),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, help_text='An identifier for the ending of the url - will be auto-generated based on the title for web pages.', null=True)),
                ('created_time', models.DateTimeField(editable=False)),
                ('updated_time', models.DateTimeField(editable=False)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('registration_start_time', models.DateTimeField(blank=True, null=True)),
                ('registration_end_time', models.DateTimeField(blank=True, null=True)),
                ('application_start_time', models.DateTimeField(blank=True, null=True)),
                ('application_end_time', models.DateTimeField(blank=True, null=True)),
                ('application_early_end_time', models.DateTimeField(blank=True, null=True)),
                ('is_advanced', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_exam_created_by', to=settings.AUTH_USER_MODEL)),
                ('previous_exams', models.ManyToManyField(blank=True, to='exam.Exam')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_exam_updated_by', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.Product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ExamRegistration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ada_requirement', models.CharField(blank=True, choices=[('', 'I do not require special test center arrangements'), ('TIME AND A HALF', 'Yes - require an additional 2 hours'), ('ADDITIONAL 30 MINUTES', 'Yes - require additional 30 minutes'), ('DOUBLE TIME', 'Yes - require an additional 4 hours'), ('READER REQUIRED', 'Yes - require reader'), ('SEPARATE ROOM', 'Yes - require separate room')], max_length=50)),
                ('verified', models.BooleanField(default=False)),
                ('code_of_ethics', models.BooleanField(default=False)),
                ('release_information', models.BooleanField(default=False)),
                ('certificate_name', models.CharField(max_length=100)),
                ('gee_eligibility_id', models.CharField(blank=True, max_length=50, null=True)),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.Exam')),
                ('purchase', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.Purchase')),
                ('registration_type', models.CharField(choices=[('CEP_A', 'CEP_A: AICP CEP'), ('CEP_T_0', 'CEP_T_0: AICP CEP Transfer from previos - no fee'), ('CEP_T_100', 'CEP_T_100: AICP CEP Transfer from previos - $150 fee'), ('CTP_A', 'CTP_A: AICP CTP'), ('CTP_T_0', 'CTP_T_0: AICP CTP Transfer from previos - no fee'), ('CTP_T_100', 'CTP_T_100: AICP CTP Transfer from previos - $150 fee'), ('CUD_A', 'CUD_A: AICP CUD'), ('CUD_T_0', 'CUD_T_0: AICP CUD Transfer from previous - no fee'), ('CUD_T_100', 'CUD_T_100: AICP CUD Transfer from previous - $150 fee'), ('MCIP_A', 'MCIP_A: Canadian Institute of Planners (MCIP)'), ('NJ_NOAICP', 'NJ_NOAICP: NJ: registering for exam, not applying for AICP'), ('NJ_REG_A', 'NJ_REG_A: registering and applied for AICP'), ('REG_A', 'REG_A: Regular Applicant - Pre Approved'), ('REG_T_0', 'REG_T_0: Transfer from previous-no fee'), ('REG_T_100', 'REG_T_100: Transfer from previous-150$ fee'), ('SCHOLAR_A', 'SCHOLAR_A: Scholarship Recipient'), ('PDO', 'PDO: Professional Development Officer registration')], max_length=20)),
                ('is_pass', models.NullBooleanField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExamApplication',
            fields=[
                ('content_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='content.Content')),
                ('application_type', models.CharField(choices=[('REG', 'Regular Applicant'), ('MCIP', 'Canadian Institute of Planners (MCIP)'), ('NJ', 'NJ: applying for AICP only, already passed exam'), ('SCHOLAR', 'SCHOLAR: (archived no longer used) '), ('NJ_REG', 'NJ: applying for AICP and will register for the exam'), ('NJ_NOAICP', 'NJ: Not Applying for AICP – Exam Only'), ('CEP', 'AICP Certified Environmental Planner'), ('CTP', 'AICP Certified Transportation Planner'), ('CUD', 'AICP Certified Urban Designer')], max_length=10)),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('application_status', models.CharField(choices=[('A', 'Approved'), ('D', 'Denied'), ('E', 'Expired or Deleted'), ('EB_D', 'Early Bird Denied'), ('I', 'Incomplete'), ('N', 'Not yet submitted'), ('P', 'Pending and under review'), ('R', 'Under review'), ('V_C', 'Verification Complete'), ('V_I', 'Verification Incomplete'), ('V_R', 'Verification Review')], max_length=10)),
                ('code_of_ethics', models.BooleanField(default=False)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.Exam')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_applications', to='myapa.IndividualContact')),
                ('current_review_round', models.IntegerField(blank=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)], null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('content.content',),
        ),
        migrations.AddField(
            model_name='applicationdegree',
            name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.ExamApplication'),
        ),
        migrations.AddField(
            model_name='applicationjobhistory',
            name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exam.ExamApplication'),
        ),
        migrations.AddField(
            model_name='examregistration',
            name='application',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='exam.ExamApplication'),
        ),
        migrations.CreateModel(
            name='ApplicationCategory',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Exam Categories',
            },
            bases=('submissions.category',),
        ),
        migrations.CreateModel(
            name='ExamApplicationOrder',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name': 'Exam application order',
            },
            bases=('store.order',),
        ),
        migrations.CreateModel(
            name='ExamRegistrationOrder',
            fields=[
            ('is_pass', models.NullBooleanField()),
            ],
            options={
                'proxy': True,
                'verbose_name': 'Exam registration order',
            },
            bases=('store.order',),
        ),
        migrations.AddField(
            model_name='examregistration',
            name='contact',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='exam_registrations', to='myapa.IndividualContact'),
            preserve_default=False,
        ),
        # migrations.AddField(
        #     model_name='applicationdegree',
        #     name='publish_status',
        #     field=models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('SUBMISSION', 'Submission'), ('EARLY_RESUBMISSION', 'Early Resubmission')], default='DRAFT', max_length=50),
        # ),
        # migrations.AddField(
        #     model_name='applicationdegree',
        #     name='publish_time',
        #     field=models.DateTimeField(blank=True, null=True, verbose_name='publish time'),
        # ),
        # migrations.AddField(
        #     model_name='applicationdegree',
        #     name='publish_uuid',
        #     field=models.CharField(blank=True, default=uuid.uuid4, max_length=36, null=True),
        # ),
        migrations.AddField(
            model_name='applicationdegree',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exam_applicationdegree_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='applicationjobhistory',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exam_applicationjobhistory_published_by', to=settings.AUTH_USER_MODEL),
        ),
        # migrations.AddField(
        #     model_name='applicationjobhistory',
        #     name='published_time',
        #     field=models.DateTimeField(blank=True, editable=False, null=True),
        # ),
        migrations.CreateModel(
            name='ExamApplicationReview',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name': 'Exam application review',
            },
            bases=('submissions.review',),
        ),
        # migrations.AlterModelOptions(
        #     name='applicationdegree',
        #     options={'permissions': (('can_publish', 'Can publish'),)},
        # ),
        # migrations.AlterModelOptions(
        #     name='applicationjobhistory',
        #     options={'permissions': (('can_publish', 'Can publish'),)},
        # ),
        migrations.CreateModel(
            name='ExamApplicationRole',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name': 'Exam application reviewer role',
            },
            bases=('submissions.reviewrole',),
        ),
        # migrations.AlterModelOptions(
        #     name='examapplicationorder',
        #     options={'verbose_name': 'Exam application order'},
        # ),
        # migrations.AlterModelOptions(
        #     name='examapplicationreview',
        #     options={'verbose_name': 'Exam application review'},
        # ),
        # migrations.AlterModelOptions(
        #     name='examregistrationorder',
        #     options={'verbose_name': 'Exam registration order'},
        # ),
        # migrations.AlterField(
        #     model_name='exam',
        #     name='status',
        #     field=models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status'),
        # ),
        # migrations.AddField(
        #     model_name='examregistration',
        #     name='is_pass',
        #     field=models.NullBooleanField(),
        # ),
    ]