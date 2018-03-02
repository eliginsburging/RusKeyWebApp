from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
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
    sorted_verb_list = sorted(Verb.objects.all(),
                              key=lambda a: a.get_earliest_due_date(request.user))
    current_user = request.user
    return render(
        request,
        'ruskeyverbs/list_view_per_user.html',
        context={'verb_list': sorted_verb_list, 'current_user': current_user}
    )


class VerbDetails(LoginRequiredMixin, generic.DetailView):
    model = Verb

# class VerbListPerUser(LoginRequiredMixin, generic.ListView):
#     model = Verb
#     template_name = 'ruskeyverbs/list_view_per_user.html'
#
#
#     def get_queryset(self):
#         print(sorted(Verb.objects.all(), key=lambda a: a.get_earliest_due_date(self.request.user)))
#         return sorted(Verb.objects.all(), key=lambda a: a.get_earliest_due_date(self.request.user))
#
        # Verb.objects.filter(
        #     example__performanceperexample__user=self.request.user).order_by('example__performanceperexample__due_date').distinct()
