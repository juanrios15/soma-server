# Generated by Django 4.2.5 on 2023-10-24 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attempts', '0004_attempt_is_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='points_obtained',
            field=models.IntegerField(default=0),
        ),
    ]