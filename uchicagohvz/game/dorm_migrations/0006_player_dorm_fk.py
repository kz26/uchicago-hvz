# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_populate_game_dorms'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='dorm_fk',
            field=models.ForeignKey(default=1, to='game.Dorm'),
            preserve_default=False,
        ),
    ]
