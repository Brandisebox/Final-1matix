# Generated by Django 4.2.20 on 2025-06-29 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onematrix', '0005_alter_payment_customer_phone_alter_payment_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='profiling_email_sent',
            field=models.BooleanField(default=False),
        ),
    ]
