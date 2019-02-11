# Generated by Django 2.1.3 on 2019-01-15 16:54

from django.conf import settings
import django.contrib.postgres.fields.citext
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('codecov_auth', '0001_initial')
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'branches',
            },
        ),
        migrations.CreateModel(
            name='Commit',
            fields=[
                ('commitid', models.TextField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updatestamp', models.DateTimeField(auto_now=True)),
                ('ci_passed', models.BooleanField()),
                ('totals', django.contrib.postgres.fields.jsonb.JSONField()),
                ('report', django.contrib.postgres.fields.jsonb.JSONField()),
                ('author', models.ForeignKey(db_column='author', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'commits',
            },
        ),
        migrations.CreateModel(
            name='Pull',
            fields=[
                ('pullid', models.IntegerField(primary_key=True, serialize=False)),
                ('issueid', models.IntegerField()),
                ('updatestamp', models.DateTimeField(auto_now=True)),
                ('state', models.CharField(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('base', models.CharField(max_length=100)),
                ('compared_to', models.CharField(max_length=100)),
                ('head', models.CharField(max_length=100)),
                ('commentid', models.CharField(max_length=100)),
                ('diff', django.contrib.postgres.fields.jsonb.JSONField()),
                ('flare', django.contrib.postgres.fields.jsonb.JSONField()),
                ('author', models.ForeignKey(db_column='author', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'pulls',
            },
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('repoid', models.IntegerField(primary_key=True, serialize=False)),
                ('service_id', models.TextField()),
                ('name', django.contrib.postgres.fields.citext.CITextField()),
                ('private', models.BooleanField()),
                ('updatestamp', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(db_column='ownerid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'repos',
            },
        ),
        migrations.CreateModel(
            name='YamlHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'yaml_history',
            },
        ),
        migrations.AddField(
            model_name='pull',
            name='repository',
            field=models.ForeignKey(db_column='repoid', on_delete=django.db.models.deletion.CASCADE, related_name='pull_requests', to='core.Repository'),
        ),
        migrations.AddField(
            model_name='commit',
            name='repository',
            field=models.ForeignKey(db_column='repoid', on_delete=django.db.models.deletion.CASCADE, related_name='commits', to='core.Repository'),
        ),
    ]
