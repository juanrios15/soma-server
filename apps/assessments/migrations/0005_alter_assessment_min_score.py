# Generated by Django 4.2.5 on 2023-09-17 07:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0004_rename_dificultad_assessmentdifficultyrating_difficulty'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='min_score',
            field=models.PositiveIntegerField(default=70, validators=[django.core.validators.MinValueValidator(60), django.core.validators.MaxValueValidator(90)]),
        ),
    ]
