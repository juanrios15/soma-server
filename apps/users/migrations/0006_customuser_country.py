# Generated by Django 4.1 on 2023-11-08 21:50

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_customuser_reset_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='country',
            field=django_countries.fields.CountryField(blank=True, max_length=2, null=True),
        ),
    ]
