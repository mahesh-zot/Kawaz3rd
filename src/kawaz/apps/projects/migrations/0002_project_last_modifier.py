# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='last_modifier',
            field=models.ForeignKey(verbose_name='Last modified by', related_name='last_modified_projects', editable=False, null=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
