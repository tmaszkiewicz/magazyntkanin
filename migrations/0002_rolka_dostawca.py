# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-05-15 12:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magazyntkanin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolka',
            name='dostawca',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
