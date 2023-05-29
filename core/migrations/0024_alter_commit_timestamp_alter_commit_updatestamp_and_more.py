# Generated by Django 4.1.7 on 2023-05-29 15:24

import core.models
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0023_alter_commitnotification_decoration_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="commit",
            name="timestamp",
            field=core.models.DateTimeWithoutTZField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="commit",
            name="updatestamp",
            field=core.models.DateTimeWithoutTZField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="commitnotification",
            name="notification_type",
            field=models.TextField(
                choices=[
                    ("comment", "Comment"),
                    ("gitter", "Gitter"),
                    ("hipchat", "Hipchat"),
                    ("irc", "Irc"),
                    ("slack", "Slack"),
                    ("status_changes", "Status Changes"),
                    ("status_patch", "Status Patch"),
                    ("status_project", "Status Project"),
                    ("webhook", "Webhook"),
                    ("codecov_slack_app", "Codecov Slack App"),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="pull",
            name="updatestamp",
            field=core.models.DateTimeWithoutTZField(default=django.utils.timezone.now),
        ),
    ]
