from django.db import models

# Create your models here.


class verb(models.Model):
    infinitive = models.CharField(max_length=30)
    trans_infinitive = models.CharField('transliterated inifinitve',
                                        max_length=35)
    aspect = models.CharField(max_length=30)
    meaning = models.CharField(max_length=200)
    first_sg = models.CharField('first person singular',
                                max_length=30)
    second_sg = models.CharField('second person singular',
                                 max_length=30)
    third_sg = models.CharField('third person singular',
                                max_length=30)
    first_pl = models.CharField('first person plural',
                                max_length=30)
