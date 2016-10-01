# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

DORMS = (
    ("BS", "Blackstone"),
    ("BR", "Breckinridge"),
    ("BV", "Broadview"),
    ("BJ", "Burton-Judson Courts"),
    ("IH", "International House"),
    ("MC", "Maclean"),
    ("MAX", "Max Palevsky"),
    ("NG", "New Graduate Residence Hall"),
    ("SH", "Snell-Hitchcock"),
    ("SC", "South Campus"),
    ("ST", "Stony Island"),
    ("OFF", "Off campus"),
    ("NC", "North Campus")
)

DORMS = {x:y for x, y in DORMS}

def set_dorm_fk(apps, schema_editor):
    Dorm = apps.get_model('game', 'Dorm')
    Player = apps.get_model('game', 'Player')
    for p in Player.objects.all():
        p.dorm_fk = Dorm.objects.get(name=DORMS[p.dorm])
        p.save(update_fields=['dorm_fk'])


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_player_dorm_fk'),
    ]

    operations = [
    	migrations.RunPython(set_dorm_fk)
    ]
