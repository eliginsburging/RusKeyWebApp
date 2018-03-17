import datetime
from django import template
from ruskeyverbs.models import Verb

register = template.Library()


@register.filter(name='overdue')
def overdue(my_verb, my_user):
    return my_verb.is_overdue(my_user)


@register.filter(name='duedate')
def due_date(my_verb, my_user):
    date = my_verb.get_earliest_due_date(my_user)
    future_date = datetime.date.today() + datetime.timedelta(weeks=9999)
    if date == future_date:
        return "Not studied yet"
    else:
        return date
