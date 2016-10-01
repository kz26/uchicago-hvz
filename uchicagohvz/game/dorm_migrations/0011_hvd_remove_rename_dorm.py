# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0010_player_remove_rename_dorm'),
    ]

    operations = [
        migrations.RemoveField('HighValueDorm', 'dorm'),
        migrations.RenameField('HighValueDorm', 'dorm_fk', 'dorm')
    ]
