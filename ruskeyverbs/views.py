from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
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


# @login_required
# def verb_list(request):
