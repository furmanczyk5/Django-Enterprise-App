# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-19 20:53
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    # replaces = [('store', '0001_squashed_0041_auto_20160312_0447'), ('store', '0002_auto_20160519_2258'), ('store', '0003_auto_20160601_2336'), ('store', '0004_productawardnomination'), ('store', '0005_auto_20160829_1622'), ('store', '0006_auto_20160913_2106'), ('store', '0007_auto_20161018_1734')]

    initial = True

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        # ('myapa', '0001_squashed_0007_auto_20161018_1735'),
('myapa', '0001_squashed_0052_auto_20160331_1650'),
        # ('content', '0001_squashed_0012_auto_20161018_1735'),
        ('content', '0001_squashed_0064_auto_20160328_1819'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_user_id', models.CharField(help_text="Contact's Imis Id", max_length=10)),
                ('is_manual', models.BooleanField(default=False, verbose_name='Is Manual Order')),
                ('submitted_time', models.DateTimeField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL)),
                ('imis_batch', models.CharField(blank=True, max_length=50, null=True)),
                ('imis_batch_time', models.DateField(blank=True, null=True)),
                ('imis_trans_number', models.IntegerField(blank=True, null=True)),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('expected_payment_method', models.CharField(blank=True, choices=[('CC', 'Credit Card'), ('CC_REFUND', 'Credit Card Refund'), ('CHECK', 'Check'), ('CHECK_REFUND', 'Check Refund'), ('REBATE', 'Chapter or division rebate'), ('CASH', 'Cash')], max_length=50, null=True)),
                ('order_status', models.CharField(choices=[('NOT_SUBMITTED', 'Not Yet Submitted'), ('SUBMITTED', 'Submitted'), ('PROCESSED', 'Processed (Written to iMIS)'), ('CANCELLED', 'Cancelled')], default='NOT_SUBMITTED', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=200, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status')),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, help_text='An identifier for the ending of the url - will be auto-generated based on the title for web pages.', null=True)),
                ('created_time', models.DateTimeField(editable=False)),
                ('updated_time', models.DateTimeField(editable=False)),
                ('user_address_num', models.IntegerField(blank=True, null=True)),
                ('address1', models.CharField(blank=True, max_length=40, null=True)),
                ('address2', models.CharField(blank=True, max_length=40, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('gl_account', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6)),
                ('submitted_time', models.DateTimeField(blank=True, null=True)),
                ('imis_trans_line_number', models.IntegerField(blank=True, null=True)),
                ('method', models.CharField(choices=[('CC', 'Credit Card'), ('CC_REFUND', 'Credit Card Refund'), ('CHECK', 'Check'), ('CHECK_REFUND', 'Check Refund'), ('REBATE', 'Chapter or division rebate'), ('CASH', 'Cash')], max_length=50)),
                ('billing_name', models.CharField(blank=True, max_length=60, null=True)),
                ('card_check_number', models.CharField(blank=True, help_text='For check or credit card payments: enter check number or credit card ending digits \n                for payments processed manually. \n                DO NOT enter full credit card numbers in this field.', max_length=50, null=True, verbose_name='Check number / credit card ending digits')),
                ('card_expires_time', models.CharField(blank=True, max_length=50, null=True, verbose_name='Credit Card expiration date')),
                ('pn_ref', models.CharField(blank=True, max_length=50, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_payment_created_by', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.Order')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_payment_updated_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('contact', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='myapa.Contact')),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('imis_batch', models.CharField(blank=True, max_length=50, null=True)),
                ('imis_batch_date', models.DateField(blank=True, null=True)),
                ('imis_trans_number', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=200, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status')),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, help_text='An identifier for the ending of the url - will be auto-generated based on the title for web pages.', null=True)),
                ('created_time', models.DateTimeField(editable=False)),
                ('updated_time', models.DateTimeField(editable=False)),
                ('product_type', models.CharField(help_text='leave blank to auto-populate', choices=[('PRODUCT', 'Default Product Type'), ('CANCELLATION', 'Cancellation/Refund'), ('CANCELLATION_FEE', 'Cancellation Fee($50)'), ('EVENT_REGISTRATION', 'Event Registration'), ('PUBLICATION_SUBSCRIPTION', 'Publication/Subscription'), ('ACTIVITY_TICKET', 'Event Activity Ticket'), ('CM_REGISTRATION', 'CM Annual Registrations'), ('CM_PER_CREDIT', 'CM Per-Credit Payments'), ('DUES', 'Membership Dues'), ('DIGITAL_PUBLICATION', 'Digital Publications'), ('CHAPTER', 'Chapter'), ('DIVISION', 'Division'), ('BOOK', 'Book'), ('DONATION', 'Donation'), ('EBOOK', 'E-book'), ('STREAMING', 'Streaming'), ('DONATION', 'Donation'), ('EXAM_APPLICATION', 'Exam Application'), ('EXAM_REGISTRATION', 'Exam Registration'), ('SHIPPING', 'Shipping'), ('TAX', 'Tax'), ('AWARD', 'Awards'), ('ADJUSTMENT', 'Adjustment'), ('JOB_AD', 'Job Ad'), ('RESEARCH_INQUIRY', 'Research Inquiry')], blank=True, max_length=50)),
                ('imis_code', models.CharField(max_length=50, null=True)),
                ('max_quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('max_quantity_per_person', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('max_quantity_standby', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('gl_account', models.CharField(max_length=50)),
                ('content', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='product', to='content.Content')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_product_created_by', to=settings.AUTH_USER_MODEL)),
                ('future_groups', models.ManyToManyField(blank=True, related_name='products_future', to='auth.Group')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_product_updated_by', to=settings.AUTH_USER_MODEL)),
                ('publish_status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('SUBMISSION', 'Submission'), ('EARLY_RESUBMISSION', 'Early Resubmission')], default='DRAFT', max_length=50)),
                ('reviews', models.TextField(blank=True, help_text='For APA-curated reviews of the product.', null=True)),
                ('shippable', models.BooleanField(default=False)),
                ('organizations_can_purchase', models.BooleanField(default=False)),
                ('individuals_can_purchase', models.BooleanField(default=True)),
                ('publish_uuid', models.CharField(blank=True, default=uuid.uuid4, max_length=36, null=True)),
                ('published_time', models.DateTimeField(blank=True, editable=False, null=True)),
                ('published_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='store_product_published_by', to=settings.AUTH_USER_MODEL)),
                ('publish_time', models.DateTimeField(blank=True, null=True, verbose_name='publish time')),
                ('refund_cutoff_time', models.DateTimeField(blank=True, help_text='If users can request refunds for this product online, then this date may be added as a cutoff for refund requests.', null=True)),
                ('current_quantity_taken', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('question_1', models.TextField(blank=True, null=True, verbose_name='custom question 1')),
                ('question_2', models.TextField(blank=True, null=True, verbose_name='custom question 2')),
                ('question_3', models.TextField(blank=True, null=True, verbose_name='custom question 3')),
                ('agreement_statement_1', models.TextField(blank=True, null=True, verbose_name='custom agreement checkbox 1')),
                ('agreement_statement_2', models.TextField(blank=True, null=True, verbose_name='custom agreement checkbox 2')),
                ('agreement_statement_3', models.TextField(blank=True, null=True, verbose_name='custom agreement checkbox 3')),
                ('email_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='content.EmailTemplate')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=200, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status')),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, help_text='An identifier for the ending of the url - will be auto-generated based on the title for web pages.', null=True)),
                ('created_time', models.DateTimeField(editable=False)),
                ('updated_time', models.DateTimeField(editable=False)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_productoption_created_by', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='store.Product')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_productoption_updated_by', to=settings.AUTH_USER_MODEL)),
                ('publish_uuid', models.CharField(blank=True, default=uuid.uuid4, max_length=36, null=True)),
                ('publish_status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('SUBMISSION', 'Submission'), ('EARLY_RESUBMISSION', 'Early Resubmission')], default='DRAFT', max_length=50)),
                ('publish_time', models.DateTimeField(blank=True, null=True, verbose_name='publish time')),
                ('published_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='store_productoption_published_by', to=settings.AUTH_USER_MODEL)),
                ('published_time', models.DateTimeField(blank=True, editable=False, null=True)),
                ('sort_number', models.PositiveIntegerField(blank=True, default=999, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=200, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status')),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, help_text='An identifier for the ending of the url - will be auto-generated based on the title for web pages.', null=True)),
                ('created_time', models.DateTimeField(editable=False)),
                ('updated_time', models.DateTimeField(editable=False)),
                ('priority', models.IntegerField(default=0)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('imis_reg_class', models.CharField(blank=True, max_length=50, null=True)),
                ('begin_time', models.DateTimeField(blank=True, null=True, verbose_name='begin time')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='end time')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_productprice_created_by', to=settings.AUTH_USER_MODEL)),
                ('exclude_groups', models.ManyToManyField(blank=True, related_name='product_prices_exclude', to='auth.Group')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='store.Product')),
                ('required_groups', models.ManyToManyField(blank=True, related_name='product_prices_require', to='auth.Group')),
                ('required_product', models.ForeignKey(blank=True, help_text='If this price requires that another product be purchased in order to receive it, enter that product here.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='price_required_by', to='store.Product', verbose_name='Other required product')),
                ('required_product_option', models.ForeignKey(blank=True, help_text='The option required for this product to get this price.', null=True, on_delete=django.db.models.deletion.CASCADE, to='store.ProductOption', verbose_name='Associated Option')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_productprice_updated_by', to=settings.AUTH_USER_MODEL)),
                ('include_search_results', models.BooleanField(default=False, help_text='show this price in the search results list')),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('publish_uuid', models.CharField(blank=True, default=uuid.uuid4, max_length=36, null=True)),
                ('publish_status', models.CharField(choices=[('DRAFT', 'Draft'), ('PUBLISHED', 'Published'), ('SUBMISSION', 'Submission'), ('EARLY_RESUBMISSION', 'Early Resubmission')], default='DRAFT', max_length=50)),
                ('publish_time', models.DateTimeField(blank=True, null=True, verbose_name='publish time')),
                ('published_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='store_productprice_published_by', to=settings.AUTH_USER_MODEL)),
                ('published_time', models.DateTimeField(blank=True, editable=False, null=True)),
                ('other_required_product_must_be_in_cart', models.BooleanField(default=False, help_text='If, an "Other required product code" is entered to the left, and that other product\n            must be purchased at the same time as this product (i.e. purchased in the same order\n            as opposed to purchased at any point in the past), then check this box')),
                ('other_required_product_code', models.CharField(blank=True, help_text='If this prices requires that the user have purchased another product in order\n            to receive this price for this product, then enter the code for that other product here', max_length=200, null=True)),
                ('other_required_option_code', models.CharField(blank=True, help_text='If, an "Other required product code" is entered to the left, and for that other product,\n            a particular option must have been choosen in order to receive this price, then enter that\n            other product\'s option code here', max_length=200, null=True)),
                ('option_code', models.CharField(blank=True, help_text='If this price applies to a particular option above, enter the code for that option here', max_length=200, null=True)),
                ('required_product_options', models.ManyToManyField(blank=True, help_text='If this price requires that specific options from another product be purchased in order to receive it, enter those options here.', related_name='prices_required_by', to='store.ProductOption', verbose_name='Other required options')),
                ('comped', models.BooleanField(default=False, verbose_name='Comped/auto-included for given required products')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(blank=True, max_length=200, null=True)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('status', models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status')),
                ('description', models.TextField(blank=True, null=True)),
                ('slug', models.SlugField(blank=True, help_text='An identifier for the ending of the url - will be auto-generated based on the title for web pages.', null=True)),
                ('created_time', models.DateTimeField(editable=False)),
                ('updated_time', models.DateTimeField(editable=False)),
                ('user_address_num', models.IntegerField(blank=True, null=True)),
                ('address1', models.CharField(blank=True, max_length=40, null=True)),
                ('address2', models.CharField(blank=True, max_length=40, null=True)),
                ('city', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.CharField(blank=True, max_length=15, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=10, null=True)),
                ('country', models.CharField(blank=True, max_length=20, null=True)),
                ('gl_account', models.CharField(max_length=50)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=6)),
                ('submitted_time', models.DateTimeField(blank=True, null=True)),
                ('imis_trans_line_number', models.IntegerField(blank=True, null=True)),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=6)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_purchase_created_by', to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.Order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='store.Product')),
                ('product_price', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='store.ProductPrice')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_purchase_updated_by', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('agreement_response_1', models.BooleanField(default=False, verbose_name='response 1')),
                ('agreement_response_2', models.BooleanField(default=False, verbose_name='response 2')),
                ('agreement_response_3', models.BooleanField(default=False, verbose_name='response 3')),
                ('question_response_1', models.CharField(blank=True, max_length=500, null=True)),
                ('question_response_2', models.CharField(blank=True, max_length=500, null=True)),
                ('question_response_3', models.CharField(blank=True, max_length=500, null=True)),
                ('expiration_time', models.DateTimeField(blank=True, null=True)),
                ('first_name', models.CharField(blank=True, max_length=20, null=True)),
                ('last_name', models.CharField(blank=True, max_length=30, null=True)),
                ('legacy_id', models.IntegerField(blank=True, null=True)),
                ('option', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='store.ProductOption')),
                ('contact', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='myapa.Contact')),
                ('contact_recipient', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='purchases_received', to='myapa.Contact')),
                ('content_master', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='purchases', to='content.MasterContent')),
                ('submitted_product_price_amount', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='amount to be charged')),
                ('imis_batch', models.CharField(blank=True, max_length=50, null=True)),
                ('imis_batch_date', models.DateField(blank=True, null=True)),
                ('imis_trans_number', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProductPublished',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40, unique=True)),
                ('last_updated', models.DateTimeField(db_index=True, default=datetime.datetime.now)),
            ],
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qty', models.PositiveIntegerField()),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.Cart')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.Product')),
            ],
        ),
        migrations.CreateModel(
            name='ProductEvent',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductCMPerCredit',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductCMRegistration',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductChapter',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductDivision',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductDues',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductSubscription',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('A', 'Active'), ('I', 'Inactive')], max_length=5)),
                ('paid_through', models.DateTimeField()),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='myapa.Contact')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='store.Product')),
            ],
        ),
        migrations.CreateModel(
            name='BookContent',
            fields=[
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Other Products',
                'proxy': True,
            },
            bases=('content.content',),
        ),
        migrations.CreateModel(
            name='ContentProduct',
            fields=[
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Other Products',
                'proxy': True,
            },
            bases=('content.content',),
        ),
        migrations.CreateModel(
            name='ProductStreaming',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductBook',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductDigitalPublication',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductEBook',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductShipping',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductTax',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductJobAd',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductExamRegistration',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductExamApplication',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        # migrations.AlterField(
        #     model_name='order',
        #     name='is_manual',
        #     field=models.BooleanField(default=False, verbose_name='Is Manual Order'),
        # ),
        # migrations.AlterField(
        #     model_name='productprice',
        #     name='comped',
        #     field=models.BooleanField(default=False, verbose_name='Comped/auto-included for given required products'),
        # ),
        migrations.CreateModel(
            name='ProductAwardNomination',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),
        migrations.CreateModel(
            name='ProductResearchInquiry',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('store.product',),
        ),        
        # migrations.AlterField(
        #     model_name='product',
        #     name='status',
        #     field=models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status'),
        # ),
        # migrations.AlterField(
        #     model_name='productoption',
        #     name='status',
        #     field=models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status'),
        # ),
        # migrations.AlterField(
        #     model_name='productprice',
        #     name='status',
        #     field=models.CharField(choices=[('A', 'Active'), ('P', 'Pending'), ('I', 'Inactive'), ('H', 'Hidden'), ('S', 'Staff-Use Only'), ('X', 'Marked for Deletion'), ('N', 'Not Complete'), ('C', 'Complete'), ('CA', 'Cancelled')], default='A', max_length=5, verbose_name='visibility status'),
        # ),
    ]