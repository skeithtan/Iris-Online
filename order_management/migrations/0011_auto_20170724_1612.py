# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-24 08:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order_management', '0010_auto_20170724_1612'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='customer_deposit_photo',
        ),
        migrations.RemoveField(
            model_name='order',
            name='customer_payment_date',
        ),
    ]
