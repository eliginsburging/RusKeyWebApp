from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Min
from django.core.exceptions import ObjectDoesNotExist
import datetime
# Create your models here.


class Verb(models.Model):
    infinitive = models.CharField(max_length=30)
    trans_infinitive = models.CharField('transliterated inifinitve',
                                        max_length=35)
    aspect = models.CharField(max_length=30)
    meaning = models.CharField(max_length=200)
    first_sg = models.CharField('first person singular', max_length=30)
    second_sg = models.CharField('second person singular', max_length=30)
    third_sg = models.CharField('third person singular', max_length=30)
    first_pl = models.CharField('first person plural', max_length=30)
    second_pl = models.CharField('second person plural', max_length=30)
    third_pl = models.CharField('third person plural', max_length=30)
    imperative_sg = models.CharField('imperative singular', max_length=30)
    imperative_pl = models.CharField('imperative plural', max_length=30)
    past_masc = models.CharField('masculine past', max_length=30)
    past_fem = models.CharField('feminine past', max_length=30)
    past_neut = models.CharField('neuter past', max_length=30)
    past_pl = models.CharField('plural past', max_length=30)
    audio_file = models.CharField(max_length=40)

    def __str__(self):
        return self.infinitive

    def get_earliest_due_date(self, my_user):
        examples = PerformancePerExample.objects.filter(user=my_user, example__verb=self).aggregate(Min('due_date'))
        future_date = datetime.date.today() + datetime.timedelta(weeks=9999)
        if examples['due_date__min'] is None:
            return future_date
        else:
            return examples['due_date__min']

    def is_overdue(self, my_user):
        return self.get_earliest_due_date(my_user) < datetime.date.today()

    def get_forms_list(self):
        return [self.infinitive.replace(chr(769),''),
                self.first_sg.replace(chr(769),''),
                self.second_sg.replace(chr(769),''),
                self.third_sg.replace(chr(769),''),
                self.first_pl.replace(chr(769),''),
                self.second_pl.replace(chr(769),''),
                self.third_pl.replace(chr(769),''),
                self.imperative_sg.replace(chr(769),''),
                self.imperative_pl.replace(chr(769),''),
                self.past_masc.replace(chr(769),''),
                self.past_fem.replace(chr(769),''),
                self.past_neut.replace(chr(769),''),
                self.past_pl.replace(chr(769),'')]


class Example(models.Model):
    verb = models.ForeignKey(Verb, on_delete=models.CASCADE)
    russian_text = models.CharField(max_length=250)
    translation_text = models.CharField(max_length=250)
    example_audio = models.CharField(max_length=40)

    def __str__(self):
        return self.translation_text


class PerformancePerExample(models.Model):
    example = models.ForeignKey(Example, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    easiness_factor = models.DecimalField(max_digits=5, decimal_places=2)
    last_interval = models.PositiveSmallIntegerField()
    date_last_studied = models.DateField(auto_now=True)
    due_date = models.DateField()

    def __str__(self):
        return str(self.due_date)


class UserState(models.Model):
    verb = models.ForeignKey(Verb, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    example_number = models.PositiveSmallIntegerField()

    def __str__(self):
        return str(self.example_number)
