# Generated by Django 3.2.5 on 2021-07-14 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="period",
            name="avoid",
            field=models.BooleanField(default=False),
        ),
    ]
