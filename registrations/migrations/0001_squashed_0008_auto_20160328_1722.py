# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-19 18:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    # replaces = [('registrations', '0001_squashed_0008_auto_20160328_1722'), ('registrations', '0002_auto_20161018_1735'), ('registrations', '0003_auto_20161019_1514')]

    initial = True

    dependencies = [
        # ('myapa', '0001_squashed_0007_auto_20161018_1735'),
('myapa', '0001_squashed_0052_auto_20160331_1650'),
        # ('store', '0001_squashed_0007_auto_20161018_1734'),
('store', '0001_squashed_0041_auto_20160312_0447'),
        # ('events', '0001_squashed_0005_event_ticket_template'),
('events', '0001_squashed_0020_event_length_in_minutes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled'), ('R', 'Refund')], default='A', max_length=5)),
                ('added_time', models.DateTimeField(editable=False)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attending', to='myapa.Contact')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendees', to='events.Event')),
                ('purchase', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attendees', to='store.Purchase')),
                ('badge_location', models.CharField(blank=True, max_length=60)),
                ('badge_name', models.CharField(blank=True, max_length=20)),
                ('badge_company', models.CharField(blank=True, max_length=60)),
                ('imis_invoice_number', models.IntegerField(blank=True, null=True)),
                ('imis_order_number', models.IntegerField(blank=True, null=True)),
                ('ready_to_print', models.BooleanField(default=False)),
                ('print_count', models.IntegerField(default=0)),
                ('last_printed_time', models.DateTimeField(blank=True, null=True)),
                ('is_standby', models.BooleanField(default=False)),
                ('address1', models.CharField(blank=True, max_length=40, null=True)),
                ('address2', models.CharField(blank=True, max_length=40, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('user_address_num', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NationalConferenceAttendee',
            fields=[
            ],
            options={
                'verbose_name': 'Conference Attendee',
                'verbose_name_plural': 'Conference Attendees',
                'proxy': True,
            },
            bases=('registrations.attendee',),
        ),
        # migrations.AlterField(
        #     model_name='attendee',
        #     name='status',
        #     field=models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled'), ('R', 'Refund')], default='A', max_length=5),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='address1',
        #     field=models.CharField(blank=True, max_length=40, null=True),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='address2',
        #     field=models.CharField(blank=True, max_length=40, null=True),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='badge_company',
        #     field=models.CharField(blank=True, max_length=60),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='city',
        #     field=models.CharField(blank=True, max_length=40, null=True),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='country',
        #     field=models.CharField(blank=True, max_length=20, null=True),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='state',
        #     field=models.CharField(blank=True, max_length=15, null=True),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='user_address_num',
        #     field=models.IntegerField(blank=True, null=True),
        # ),
        # migrations.AddField(
        #     model_name='attendee',
        #     name='zip_code',
        #     field=models.CharField(blank=True, max_length=10, null=True),
        # ),
    ]
