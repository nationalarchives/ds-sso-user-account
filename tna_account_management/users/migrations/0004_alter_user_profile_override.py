# Generated by Django 3.2.13 on 2022-06-17 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_simplify_name_fields_and_add_profile_override"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="profile_override",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text="When set, self.profile will return this value instead of fetching real profile data from Auth0.",
                null=True,
            ),
        ),
    ]
