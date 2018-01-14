# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2018-01-14 05:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assistant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.IntegerField(default=0)),
                ('classroom_id', models.IntegerField(default=0)),
                ('lesson', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Bug',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('file', models.FileField(upload_to=b'')),
                ('author_id', models.IntegerField(default=0)),
                ('classroom_id', models.IntegerField(default=0)),
                ('body', models.TextField()),
                ('publish', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ('-publish',),
            },
        ),
        migrations.CreateModel(
            name='Debug',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bug_id', models.IntegerField(default=0)),
                ('author_id', models.IntegerField(default=0)),
                ('file', models.FileField(upload_to=b'')),
                ('body', models.TextField()),
                ('publish', models.DateTimeField(auto_now_add=True)),
                ('reward', models.IntegerField(default=-1)),
                ('reward_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-publish',),
            },
        ),
        migrations.CreateModel(
            name='Enroll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_id', models.IntegerField(default=0)),
                ('classroom_id', models.IntegerField(default=0)),
                ('seat', models.IntegerField(default=0)),
                ('group', models.IntegerField(default=0)),
                ('group_show', models.IntegerField(default=0)),
                ('certificate1', models.BooleanField(default=False)),
                ('certificate1_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('certificate2', models.BooleanField(default=False)),
                ('certificate2_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('certificate3', models.BooleanField(default=False)),
                ('certificate3_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('certificate4', models.BooleanField(default=False)),
                ('certificate4_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('score_memo1', models.IntegerField(default=0)),
                ('score_memo2', models.IntegerField(default=0)),
                ('score_memo3', models.IntegerField(default=0)),
                ('score_memo4', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='EnrollGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('classroom_id', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam_id', models.IntegerField(default=0)),
                ('student_id', models.IntegerField(default=0)),
                ('answer', models.CharField(max_length=10)),
                ('score', models.IntegerField(default=0)),
                ('publication_date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(default=0)),
                ('index', models.IntegerField()),
                ('file', models.FileField(upload_to=b'')),
                ('memo', models.TextField()),
                ('publication_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('score', models.IntegerField(default=-1)),
                ('scorer', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='WorkFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_id', models.IntegerField(default=0)),
                ('filename', models.TextField()),
                ('upload_date', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='enroll',
            unique_together=set([('student_id', 'classroom_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='assistant',
            unique_together=set([('student_id', 'classroom_id', 'lesson')]),
        ),
    ]
