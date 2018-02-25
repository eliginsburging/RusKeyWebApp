# Generated by Django 2.0.2 on 2018-02-25 03:26

from django.db import migrations
from django.utils import timezone
import random
import datetime


def populate_user(apps, schema_editor):
    example_model = apps.get_model("ruskeyverbs", "Example")
    user_model = apps.get_model("auth", "User")
    performance_model = apps.get_model("ruskeyverbs", "PerformancePerExample")
    my_user = user_model.objects.get(pk=1)
    dictkey = 0
    object_dict = {}
    for i in range(example_model.objects.all().count()):
        my_example = example_model.objects.get(id=i)
        random_int = random.randint(1, 10)
        random_int_days = random.randint(1, 5)
        study_date = timezone.now() - datetime.timedelta(days=random_int_days)
        due_date = study_date + datetime.timedelta(days=random_int)
        object_dict[dictkey] = performance_model(my_example,
                                                 my_user,
                                                 2.5,
                                                 random_int,
                                                 study_date,
                                                 due_date)
        object_dict[dictkey].save()
        dictkey += 1


class Migration(migrations.Migration):

    dependencies = [
        ('ruskeyverbs', '0004_auto_20180224_2057'),
    ]

    operations = [
        migrations.RunPython(populate_user),
    ]