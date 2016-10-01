# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_game_dorms(apps, schema_editor):
	Dorm = apps.get_model('game', 'Dorm')
	Game = apps.get_model('game', 'Game')
	dorms = Dorm.objects.all()
	for g in Game.objects.all():
		for d in dorms:
			g.dorms.add(d)


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_auto_20160930_1940'),
    ]

    operations = [
    	migrations.RunPython(populate_game_dorms)
    ]
