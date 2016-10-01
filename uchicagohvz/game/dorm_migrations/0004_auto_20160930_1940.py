# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_populate_dorms'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='new_squad',
            options={'verbose_name': 'New-style squad', 'verbose_name_plural': 'New-style squads'},
        ),
        migrations.AlterModelOptions(
            name='squad',
            options={'verbose_name': 'Old-style squad', 'verbose_name_plural': 'Old-style squads'},
        ),
        migrations.AddField(
            model_name='game',
            name='dorms',
            field=models.ManyToManyField(to='game.Dorm'),
        ),
    ]
