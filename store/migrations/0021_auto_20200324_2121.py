# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-03-25 02:21
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0020_auto_20200124_1048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='payment',
            name='contact',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapa.Contact'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_payment_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.Order'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_payment_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='content',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='product', to='content.Content'),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_product_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='email_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='content.EmailTemplate'),
        ),
        migrations.AlterField(
            model_name='product',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='store_product_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_product_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='productoption',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_productoption_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='productoption',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='store_productoption_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='productoption',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_productoption_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='productprice',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_productprice_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='productprice',
            name='published_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='store_productprice_published_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='productprice',
            name='required_product',
            field=models.ForeignKey(blank=True, help_text='If this price requires that another product be purchased in order to receive it, enter that product here.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='price_required_by', to='store.Product', verbose_name='Other required product'),
        ),
        migrations.AlterField(
            model_name='productprice',
            name='required_product_option',
            field=models.ForeignKey(blank=True, help_text='The option required for this product to get this price.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.ProductOption', verbose_name='Associated Option'),
        ),
        migrations.AlterField(
            model_name='productprice',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_productprice_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='contact',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapa.Contact'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='contact_recipient',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases_received', to='myapa.Contact'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='content_master',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='content.MasterContent'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_purchase_created_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases', to='store.ProductOption'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.Order'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='store.Product'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='product_price',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='store.ProductPrice'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='store_purchase_updated_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]