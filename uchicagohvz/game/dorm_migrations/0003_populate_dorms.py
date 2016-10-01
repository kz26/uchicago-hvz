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

def populate_dorms(apps, schema_editor):
	Dorm = apps.get_model('game', 'Dorm')
	for dorm in DORMS:
		Dorm.objects.create(name=dorm[1])
		

class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_dorm'),
    ]

    operations = [
    	migrations.RunPython(populate_dorms)
    ]
