# Generated by Django 3.2.13 on 2022-07-01 18:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_user_is_social"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="email",
        ),
        migrations.RemoveField(
            model_name="user",
            name="email_verified",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_social",
        ),
        migrations.RemoveField(
            model_name="user",
            name="name",
        ),
    ]
