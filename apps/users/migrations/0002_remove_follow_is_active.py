# Generated by Django 4.2.5 on 2023-09-20 01:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follow',
            name='is_active',
        ),
    ]