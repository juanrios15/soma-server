# Generated by Django 4.2.5 on 2023-10-22 04:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='average_score',
            field=models.FloatField(default=0),
        ),
    ]