# Generated by Django 4.2.20 on 2025-06-27 18:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0055_attendancerule_company'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendancerule',
            name='name',
        ),
    ]
