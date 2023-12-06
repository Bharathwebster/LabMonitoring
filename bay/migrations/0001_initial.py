# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=225, null=True, blank=True)),
                ('mac_id', models.CharField(max_length=225)),
                ('location', models.CharField(max_length=225, null=True, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Logging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(default=b'ID', max_length=200, null=True, blank=True, choices=[(b'PR', b'Productive'), (b'IN', b'Installation/Config'), (b'ID', b'Idle'), (b'VA', b'Vacant'), (b'MA', b'Maintenance')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=225, null=True, blank=True)),
                ('description', models.CharField(max_length=225, null=True, blank=True)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=225)),
                ('status', models.CharField(default=b'ID', max_length=200, null=True, blank=True, choices=[(b'PR', b'Productive'), (b'IN', b'Installation/Config'), (b'ID', b'Idle'), (b'VA', b'Vacant'), (b'MA', b'Maintenance')])),
                ('maintenance_status', models.CharField(blank=True, max_length=200, null=True, choices=[(b'SC', b'Scheduled'), (b'US', b'UnScheduled')])),
                ('image', models.ImageField(upload_to=b'', null=True, verbose_name=b'Upload Image', blank=True)),
                ('bay_number', models.CharField(max_length=255, null=True, blank=True)),
                ('is_active', models.BooleanField(default=False)),
                ('bay', models.ForeignKey(default=False, to='bay.Bay', null=True)),
                ('current_project', models.ForeignKey(related_name='CurrentProject', blank=True, to='bay.Project', null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ToolCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category_name', models.CharField(max_length=100, null=True)),
                ('percentage', models.IntegerField(default=0, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ToolImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.FileField(upload_to=b'')),
            ],
        ),
        migrations.CreateModel(
            name='ToolProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('is_enabled', models.BooleanField(default=False)),
                ('project', models.ForeignKey(to='bay.Project')),
                ('tool', models.ForeignKey(to='bay.Tool')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='tool',
            name='projects',
            field=models.ManyToManyField(related_name='ToolProject', through='bay.ToolProject', to='bay.Project'),
        ),
        migrations.AddField(
            model_name='tool',
            name='tool_category',
            field=models.ForeignKey(blank=True, to='bay.ToolCategory', null=True),
        ),
        migrations.AddField(
            model_name='tool',
            name='tool_owner',
            field=models.ForeignKey(related_name='ToolOwner', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='tool',
            name='tool_users',
            field=models.ManyToManyField(related_name='ToolUser', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='logging',
            name='project',
            field=models.ForeignKey(to='bay.Project'),
        ),
        migrations.AddField(
            model_name='logging',
            name='tool',
            field=models.ForeignKey(to='bay.Tool'),
        ),
        migrations.AddField(
            model_name='logging',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
