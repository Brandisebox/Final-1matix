# Generated by Django 4.2.20 on 2025-06-29 19:29

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('User', '0020_user_excluded_apps'),
        ('onematrix', '0004_payment_excluded_apps'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='customer_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('PROCESSING', 'Processing'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')], default='PENDING', max_length=20),
        ),
        migrations.CreateModel(
            name='ProfileSetupToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('otp', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='User.user')),
            ],
        ),
    ]
