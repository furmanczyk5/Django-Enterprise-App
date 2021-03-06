# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-07-30 21:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('component_sites', '0012_auto_20190724_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='chapterhomepage',
            name='og_description',
            field=models.TextField(blank=True, help_text='Description for shared link.', null=True),
        ),
        migrations.AddField(
            model_name='chapterhomepage',
            name='og_image',
            field=models.ForeignKey(blank=True, help_text='Image for shared link.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='component_sites.ComponentImage'),
        ),
        migrations.AddField(
            model_name='chapterhomepage',
            name='og_type',
            field=models.CharField(choices=[('article', 'article'), ('book', 'book'), ('books.author', 'books.author'), ('books.book', 'books.book'), ('books.genre', 'books.genre'), ('business.business', 'business.business'), ('fitness.course', 'fitness.course'), ('game.achievement', 'game.achievement'), ('music.album', 'music.album'), ('music.playlist', 'music.playlist'), ('music.radio_station', 'music.radio_station'), ('music.song', 'music.song'), ('place', 'place'), ('product', 'product'), ('product.group', 'product.group'), ('product.item', 'product.item'), ('profile', 'profile'), ('restaurant.menu', 'restaurant.menu'), ('restaurant.menu_item', 'restaurant.menu_item'), ('restaurant.menu_section', 'restaurant.menu_section'), ('restaurant.restaurant', 'restaurant.restaurant'), ('video.episode', 'video.episode'), ('video.movie', 'video.movie'), ('video.other', 'video.other'), ('video.tv_show', 'video.tv_show')], default='article', max_length=50),
        ),
        migrations.AddField(
            model_name='divisionhomepage',
            name='og_description',
            field=models.TextField(blank=True, help_text='Description for shared link.', null=True),
        ),
        migrations.AddField(
            model_name='divisionhomepage',
            name='og_image',
            field=models.ForeignKey(blank=True, help_text='Image for shared link.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='component_sites.ComponentImage'),
        ),
        migrations.AddField(
            model_name='divisionhomepage',
            name='og_type',
            field=models.CharField(choices=[('article', 'article'), ('book', 'book'), ('books.author', 'books.author'), ('books.book', 'books.book'), ('books.genre', 'books.genre'), ('business.business', 'business.business'), ('fitness.course', 'fitness.course'), ('game.achievement', 'game.achievement'), ('music.album', 'music.album'), ('music.playlist', 'music.playlist'), ('music.radio_station', 'music.radio_station'), ('music.song', 'music.song'), ('place', 'place'), ('product', 'product'), ('product.group', 'product.group'), ('product.item', 'product.item'), ('profile', 'profile'), ('restaurant.menu', 'restaurant.menu'), ('restaurant.menu_item', 'restaurant.menu_item'), ('restaurant.menu_section', 'restaurant.menu_section'), ('restaurant.restaurant', 'restaurant.restaurant'), ('video.episode', 'video.episode'), ('video.movie', 'video.movie'), ('video.other', 'video.other'), ('video.tv_show', 'video.tv_show')], default='article', max_length=50),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_description',
            field=models.TextField(blank=True, help_text='Description for shared link.', null=True),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_image',
            field=models.ForeignKey(blank=True, help_text='Image for shared link.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='component_sites.ComponentImage'),
        ),
        migrations.AddField(
            model_name='landingpage',
            name='og_type',
            field=models.CharField(choices=[('article', 'article'), ('book', 'book'), ('books.author', 'books.author'), ('books.book', 'books.book'), ('books.genre', 'books.genre'), ('business.business', 'business.business'), ('fitness.course', 'fitness.course'), ('game.achievement', 'game.achievement'), ('music.album', 'music.album'), ('music.playlist', 'music.playlist'), ('music.radio_station', 'music.radio_station'), ('music.song', 'music.song'), ('place', 'place'), ('product', 'product'), ('product.group', 'product.group'), ('product.item', 'product.item'), ('profile', 'profile'), ('restaurant.menu', 'restaurant.menu'), ('restaurant.menu_item', 'restaurant.menu_item'), ('restaurant.menu_section', 'restaurant.menu_section'), ('restaurant.restaurant', 'restaurant.restaurant'), ('video.episode', 'video.episode'), ('video.movie', 'video.movie'), ('video.other', 'video.other'), ('video.tv_show', 'video.tv_show')], default='article', max_length=50),
        ),
        migrations.AddField(
            model_name='newspage',
            name='og_description',
            field=models.TextField(blank=True, help_text='Description for shared link.', null=True),
        ),
        migrations.AddField(
            model_name='newspage',
            name='og_image',
            field=models.ForeignKey(blank=True, help_text='Image for shared link.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='component_sites.ComponentImage'),
        ),
        migrations.AddField(
            model_name='newspage',
            name='og_type',
            field=models.CharField(choices=[('article', 'article'), ('book', 'book'), ('books.author', 'books.author'), ('books.book', 'books.book'), ('books.genre', 'books.genre'), ('business.business', 'business.business'), ('fitness.course', 'fitness.course'), ('game.achievement', 'game.achievement'), ('music.album', 'music.album'), ('music.playlist', 'music.playlist'), ('music.radio_station', 'music.radio_station'), ('music.song', 'music.song'), ('place', 'place'), ('product', 'product'), ('product.group', 'product.group'), ('product.item', 'product.item'), ('profile', 'profile'), ('restaurant.menu', 'restaurant.menu'), ('restaurant.menu_item', 'restaurant.menu_item'), ('restaurant.menu_section', 'restaurant.menu_section'), ('restaurant.restaurant', 'restaurant.restaurant'), ('video.episode', 'video.episode'), ('video.movie', 'video.movie'), ('video.other', 'video.other'), ('video.tv_show', 'video.tv_show')], default='article', max_length=50),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='og_description',
            field=models.TextField(blank=True, help_text='Description for shared link.', null=True),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='og_image',
            field=models.ForeignKey(blank=True, help_text='Image for shared link.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='component_sites.ComponentImage'),
        ),
        migrations.AddField(
            model_name='standardpage',
            name='og_type',
            field=models.CharField(choices=[('article', 'article'), ('book', 'book'), ('books.author', 'books.author'), ('books.book', 'books.book'), ('books.genre', 'books.genre'), ('business.business', 'business.business'), ('fitness.course', 'fitness.course'), ('game.achievement', 'game.achievement'), ('music.album', 'music.album'), ('music.playlist', 'music.playlist'), ('music.radio_station', 'music.radio_station'), ('music.song', 'music.song'), ('place', 'place'), ('product', 'product'), ('product.group', 'product.group'), ('product.item', 'product.item'), ('profile', 'profile'), ('restaurant.menu', 'restaurant.menu'), ('restaurant.menu_item', 'restaurant.menu_item'), ('restaurant.menu_section', 'restaurant.menu_section'), ('restaurant.restaurant', 'restaurant.restaurant'), ('video.episode', 'video.episode'), ('video.movie', 'video.movie'), ('video.other', 'video.other'), ('video.tv_show', 'video.tv_show')], default='article', max_length=50),
        ),
    ]
