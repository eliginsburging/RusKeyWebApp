from django.db import models
from django.contrib.auth.models import User

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
