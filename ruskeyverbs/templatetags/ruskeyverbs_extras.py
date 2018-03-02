from django import template
from ruskeyverbs.models import Verb

register = template.Library()


@register.filter(name='overdue')
def overdue(my_verb, my_user):
    return my_verb.is_overdue(my_user)


@register.filter(name='duedate')
def due_date(my_verb, my_user):
    return my_verb.due_date_for_display(my_user)
