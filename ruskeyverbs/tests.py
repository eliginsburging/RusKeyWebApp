from django.test import TestCase
from ruskeyverbs.models import Verb, Example, PerformancePerExample
from django.contrib.auth.models import User
import datetime
# Create your tests here.


class GetDueDateTest(TestCase):
    def setUp(self):
        User.objects.create_user(username="Emma", password="abc")
        PerformancePerExample.objects.create(example=Example.objects.get(
            pk=1),
                                             user=User.objects.get(
                                                 username="Emma"),
                                             easiness_factor=2.5,
                                             last_interval=1,
                                             date_last_studied=datetime.date(
                                                 year=2017,
                                                 month=3,
                                                 day=15
                                             ),
                                             due_date=datetime.date(
                                                 year=2017,
                                                 month=3,
                                                 day=17
                                             ))
        PerformancePerExample.objects.create(
            example=Example.objects.get(pk=9),
            user=User.objects.get(username="Emma"),
            easiness_factor=2.5,
            last_interval=1,
            date_last_studied=datetime.date(
                year=2017,
                month=3,
                day=15
            ),
            due_date=datetime.date(
                year=2017,
                month=3,
                day=17))
        PerformancePerExample.objects.create(
            example=Example.objects.get(pk=10),
            user=User.objects.get(username="Emma"),
            easiness_factor=2.5,
            last_interval=1,
            date_last_studied=datetime.date(
                year=2017,
                month=3,
                day=15
            ),
            due_date=datetime.date(
                year=2017,
                month=3,
                day=18))
        PerformancePerExample.objects.create(
            example=Example.objects.get(pk=11),
            user=User.objects.get(username="Emma"),
            easiness_factor=2.5,
            last_interval=1,
            date_last_studied=datetime.date(
                year=2017,
                month=3,
                day=15
            ),
            due_date=datetime.date(
                year=2017,
                month=3,
                day=19))

    def test_get_earliest_due_date_one_data_point(self):
        my_verb = Verb.objects.get(pk=1)
        my_second_verb = Verb.objects.get(pk=2)
        my_user = User.objects.get(username="Emma")
        self.assertEqual(my_verb.get_earliest_due_date(my_user), datetime.date(
            year=2017,
            month=3,
            day=17))
        self.assertEqual(my_second_verb.get_earliest_due_date(my_user),
                         datetime.date(
            year=2017,
            month=3,
            day=17))
