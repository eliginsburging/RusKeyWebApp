from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Min
from django.core.exceptions import ObjectDoesNotExist
from random import shuffle
import datetime
import decimal
# Create your models here.

stress_mark = chr(769)

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

    def remove_stress(self, word):
        return word.replace(stress_mark, '')

    def get_earliest_due_date(self, my_user):
        examples = PerformancePerExample.objects.filter(user=my_user, example__verb=self).aggregate(Min('due_date'))
        future_date = datetime.date.today() + datetime.timedelta(weeks=9999)
        if examples['due_date__min'] is None:
            return future_date
        else:
            return examples['due_date__min']

    def is_overdue(self, my_user):
        return self.get_earliest_due_date(my_user) < datetime.date.today()

    def get_forms_list(self, stressed=True, random=False):
        stressed_list = [self.infinitive,
                         self.first_sg,
                         self.second_sg,
                         self.third_sg,
                         self.first_pl,
                         self.second_pl,
                         self.third_pl,
                         self.imperative_sg,
                         self.imperative_pl,
                         self.past_masc,
                         self.past_fem,
                         self.past_neut,
                         self.past_pl]
        if not stressed:
            unstressed_list = []
            for form in stressed_list:
                unstressed_list.append(self.remove_stress(form))
        if random and stressed:
            shuffle(stressed_list)
            return stressed_list
        elif random and not stressed:
            shuffle(unstressed_list)
            return unstressed_list
        elif stressed:
            return stressed_list
        else:
            return unstressed_list


class Example(models.Model):
    verb = models.ForeignKey(Verb, on_delete=models.CASCADE)
    russian_text = models.CharField(max_length=250)
    translation_text = models.CharField(max_length=250)
    example_audio = models.CharField(max_length=40)

    def __str__(self):
        return self.verb.infinitive + ' ' + self.translation_text


class PerformancePerExample(models.Model):
    example = models.ForeignKey(Example, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    easiness_factor = models.DecimalField(max_digits=5, decimal_places=2)
    last_interval = models.PositiveSmallIntegerField()
    date_last_studied = models.DateField(auto_now=True)
    due_date = models.DateField()

    def __str__(self):
        return (str(self.due_date)
                + ' '
                + str(self.example.verb.infinitive)
                + ' '
                + self.example.translation_text)

    def update_interval(self, score):
        """
        takes a score; updates the PerformancePerExample instance based on the
        SM2 algorithm
        """
        # if the user did very poorly, next study date will be one day out
        if score*5 < 3.5:
            self.last_interval = 1
        else:
            # otherwise, update the last_interval and easiness_factor per SM2
            if self.last_interval == 1:
                self.last_interval = 2
            elif self.last_interval == 2:
                self.last_interval = 6
            else:
                self.easiness_factor += decimal.Decimal(
                    0.1-(5-(score*5))
                    * (0.08+(5-(score*5))*0.02))
                if self.easiness_factor < 1.3:
                    self.easiness_factor = decimal.Decimal(1.3)
                elif self.easiness_factor > 5:
                    self.easiness_factor = 5
                last_int = self.last_interval * self.easiness_factor
                self.last_interval = int(last_int)
        self.date_last_studied = datetime.date.today()
        self.due_date = (datetime.date.today()
                         + datetime.timedelta(days=self.last_interval))
        self.save()
