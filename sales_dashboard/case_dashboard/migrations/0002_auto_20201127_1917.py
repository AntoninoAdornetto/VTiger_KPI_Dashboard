# Generated by Django 3.0.3 on 2020-11-27 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case_dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cases',
            name='assigned_groupname',
            field=models.CharField(default='groupname', max_length=75),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cases',
            name='assigned_username',
            field=models.CharField(default='username', max_length=75),
            preserve_default=False,
        ),
    ]