# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import uchicagohvz.overwrite_fs
from django.conf import settings
import django.utils.timezone
import uchicagohvz.game.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('points', models.FloatField(help_text=b'Can be negative, e.g. to penalize players')),
                ('code', models.CharField(help_text=b'leave blank for automatic (re-)generation', max_length=255, blank=True)),
                ('redeem_limit', models.IntegerField(help_text=b'Maximum number of players that can redeem award via code entry (set to 0 for awards to be added by moderators only)')),
                ('redeem_type', models.CharField(max_length=1, choices=[(b'H', b'Humans only'), (b'Z', b'Zombies only'), (b'A', b'All players')])),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('registration_date', models.DateTimeField()),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('rules', models.FileField(storage=uchicagohvz.overwrite_fs.OverwriteFileSystemStorage(), upload_to=uchicagohvz.game.models.gen_rules_filename)),
                ('picture', models.FileField(storage=uchicagohvz.overwrite_fs.OverwriteFileSystemStorage(), null=True, upload_to=uchicagohvz.game.models.gen_pics_filename, blank=True)),
                ('color', models.CharField(default=b'#FFFFFF', max_length=64)),
                ('flavor', models.TextField(default=b'', max_length=6000)),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='HighValueDorm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dorm', models.CharField(max_length=4, choices=[(b'BJ', b'Burton-Judson Courts'), (b'IH', b'International House'), (b'MAX', b'Max Palevsky'), (b'NC', b'North Campus'), (b'SH', b'Snell-Hitchcock'), (b'SC', b'South Campus'), (b'ST', b'Stony Island'), (b'OFF', b'Off campus')])),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('points', models.IntegerField(default=3)),
                ('game', models.ForeignKey(to='game.Game')),
            ],
        ),
        migrations.CreateModel(
            name='HighValueTarget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('kill_points', models.IntegerField(default=3, help_text=b'# of points zombies receive for killing this HVT')),
                ('award_points', models.IntegerField(default=0, help_text=b'# of points the HVT earns if he/she survives for the entire duration')),
            ],
        ),
        migrations.CreateModel(
            name='Kill',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('points', models.IntegerField(default=1)),
                ('notes', models.TextField(blank=True)),
                ('lat', models.FloatField(null=True, verbose_name=b'latitude', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name=b'longitude', blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('hvd', models.ForeignKey(related_name='kills', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'High-value Dorm', blank=True, to='game.HighValueDorm', null=True)),
                ('hvt', models.OneToOneField(related_name='kill', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='game.HighValueTarget', verbose_name=b'High-value target')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='Mission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=63)),
                ('description', models.CharField(max_length=255)),
                ('summary', models.TextField(default=b'', max_length=6000)),
                ('zombies_win', models.BooleanField(default=False)),
                ('awards', models.ManyToManyField(help_text=b'Awards associated with this mission.', related_name='missions', to='game.Award', blank=True)),
                ('game', models.ForeignKey(related_name='missions', to='game.Game')),
            ],
        ),
        migrations.CreateModel(
            name='MissionPicture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('picture', models.FileField(storage=uchicagohvz.overwrite_fs.OverwriteFileSystemStorage(), upload_to=uchicagohvz.game.models.gen_pics_filename)),
                ('lat', models.FloatField(null=True, verbose_name=b'latitude', blank=True)),
                ('lng', models.FloatField(null=True, verbose_name=b'longitude', blank=True)),
                ('game', models.ForeignKey(related_name='pictures', to='game.Game')),
            ],
        ),
        migrations.CreateModel(
            name='New_Squad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('game', models.ForeignKey(related_name='new_squads', to='game.Game')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False)),
                ('bite_code', models.CharField(help_text=b'leave blank for automatic (re-)generation', max_length=255, blank=True)),
                ('dorm', models.CharField(max_length=4, choices=[(b'BJ', b'Burton-Judson Courts'), (b'IH', b'International House'), (b'MAX', b'Max Palevsky'), (b'NC', b'North Campus'), (b'SH', b'Snell-Hitchcock'), (b'SC', b'South Campus'), (b'ST', b'Stony Island'), (b'OFF', b'Off campus')])),
                ('major', models.CharField(help_text=b'autopopulates from LDAP', max_length=255, blank=True)),
                ('human', models.BooleanField(default=True)),
                ('opt_out_hvt', models.BooleanField(default=False)),
                ('gun_requested', models.BooleanField(default=False)),
                ('renting_gun', models.BooleanField(default=False)),
                ('gun_returned', models.BooleanField(default=False)),
                ('last_words', models.CharField(max_length=255, blank=True)),
                ('lead_zombie', models.BooleanField(default=False)),
                ('delinquent_gun', models.BooleanField(default=False)),
                ('game', models.ForeignKey(related_name='players', to='game.Game')),
                ('new_squad', models.ForeignKey(related_name='players', blank=True, to='game.New_Squad', null=True)),
            ],
            options={
                'ordering': ['-game__start_date', 'user__username', 'user__last_name', 'user__first_name'],
            },
        ),
        migrations.CreateModel(
            name='Squad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('game', models.ForeignKey(related_name='squads', to='game.Game')),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='squad',
            field=models.ForeignKey(related_name='players', blank=True, to='game.Squad', null=True),
        ),
        migrations.AddField(
            model_name='player',
            name='user',
            field=models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='missionpicture',
            name='players',
            field=models.ManyToManyField(help_text=b'Players in this picture.', related_name='pictures', to='game.Player', blank=True),
        ),
        migrations.AddField(
            model_name='kill',
            name='killer',
            field=models.ForeignKey(related_name='+', to='game.Player'),
        ),
        migrations.AddField(
            model_name='kill',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, editable=False, to='game.Kill', null=True),
        ),
        migrations.AddField(
            model_name='kill',
            name='victim',
            field=models.ForeignKey(related_name='+', to='game.Player'),
        ),
        migrations.AddField(
            model_name='highvaluetarget',
            name='player',
            field=models.OneToOneField(related_name='hvt', to='game.Player'),
        ),
        migrations.AddField(
            model_name='award',
            name='game',
            field=models.ForeignKey(related_name='+', to='game.Game'),
        ),
        migrations.AddField(
            model_name='award',
            name='players',
            field=models.ManyToManyField(help_text=b'Players that should receive this award.', related_name='awards', to='game.Player', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='squad',
            unique_together=set([('game', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='player',
            unique_together=set([('game', 'bite_code'), ('user', 'game')]),
        ),
        migrations.AlterUniqueTogether(
            name='new_squad',
            unique_together=set([('game', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='mission',
            unique_together=set([('game', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='kill',
            unique_together=set([('parent', 'killer', 'victim')]),
        ),
        migrations.AlterUniqueTogether(
            name='highvaluedorm',
            unique_together=set([('game', 'dorm')]),
        ),
        migrations.AlterUniqueTogether(
            name='award',
            unique_together=set([('game', 'name'), ('game', 'code')]),
        ),
    ]
