# Generated by Django 5.2 on 2025-06-28 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_classsession_attendancelog_session_subject_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classsession',
            name='subject',
        ),
        migrations.RemoveField(
            model_name='student',
            name='user',
        ),
        migrations.RemoveField(
            model_name='subject',
            name='owner',
        ),
        migrations.DeleteModel(
            name='AttendanceLog',
        ),
        migrations.DeleteModel(
            name='ClassSession',
        ),
        migrations.DeleteModel(
            name='Student',
        ),
        migrations.DeleteModel(
            name='Subject',
        ),
    ]
