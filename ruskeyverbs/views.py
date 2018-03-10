from itertools import chain
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.db.models import Min
from django.db.models import Q
from .models import Verb, Example, PerformancePerExample

# Create your views here.


def index(request):
    """
    View function for home page
    """
    num_verbs = Verb.objects.all().count()
    num_examples = Example.objects.all().count()
    return render(
        request,
        'ruskeyverbs/index.html',
        context={'num_verbs': num_verbs, 'num_examples': num_examples}
    )


@login_required
def VerbListPerUser(request):
    # get list of all available verbs sorted by due date for given user
    verbs_with_due_dates = Verb.objects.annotate(due=Min('example__performanceperexample__due_date', filter=Q(example__performanceperexample__user_id=request.user.pk))).order_by('due').exclude(due=None)
    verbs_without_due_dates = Verb.objects.annotate(due=Min('example__performanceperexample__due_date', filter=Q(example__performanceperexample__user_id=request.user.pk))).order_by('due').exclude(~Q(due=None))
    sorted_verb_list = list(chain(verbs_with_due_dates, verbs_without_due_dates))
    # sorted_verb_list = sorted(Verb.objects.all(),
    #                           key=lambda a: a.get_earliest_due_date(request.user))
    current_user = request.user
    return render(
        request,
        'ruskeyverbs/list_view_per_user.html',
        context={'verb_list': sorted_verb_list, 'current_user': current_user}
    )


class VerbDetails(LoginRequiredMixin, generic.DetailView):
    model = Verb
