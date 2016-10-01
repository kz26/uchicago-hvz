# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_set_hvd_fk'),
    ]

    operations = [
        migrations.RemoveField('Player', 'dorm'),
        migrations.RenameField('Player', 'dorm_fk', 'dorm')
    ]
