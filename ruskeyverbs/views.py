from itertools import chain
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import generic
from django.db.models import Min
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from fuzzywuzzy import fuzz
from random import shuffle
from .models import Verb, Example, PerformancePerExample
from .forms import FillInTheBlankForm, ArrangeWordsForm


def strip_punct_lower(some_string, stressed=False):
    """
    helper function that takes a string and returns the same string in lower
    case with all punctuation marks stripped
    """
    some_string = some_string.replace(',', '')
    some_string = some_string.replace('.', '')
    some_string = some_string.replace('?', '')
    some_string = some_string.replace('!', '')
    some_string = some_string.replace(';', '')
    some_string = some_string.replace(':', '')
    if not stressed:
        some_string = some_string.replace(chr(769), '')
    some_string = some_string.lower()
    return some_string


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
    verbs_with_due_dates = Verb.objects.annotate(due=Min('example__performanceperexample__due_date',
                                                         filter=Q(example__performanceperexample__user_id=request.user.pk))).order_by('due').exclude(due=None)
    verbs_without_due_dates = Verb.objects.annotate(due=Min('example__performanceperexample__due_date',
                                                            filter=Q(example__performanceperexample__user_id=request.user.pk))).exclude(~Q(due=None))
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


@login_required
def FillInTheBlank(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    verb_inst = example_inst.verb
    russian_text = example_inst.russian_text
    russian_text_list = strip_punct_lower(russian_text)
    russian_text_list = russian_text_list.split()
    russian_text_list_stressed = strip_punct_lower(russian_text, stressed=True).split()
    for i in range(len(russian_text_list)):
        if russian_text_list[i] in verb_inst.get_forms_list():
            answer = russian_text_list[i]
            stressed_answer = russian_text_list_stressed[i]
    russian_text
    russian_text = russian_text.replace(stressed_answer, '_________')
    russian_text = russian_text.replace(stressed_answer.capitalize(), '_________')
    example_audio_file = example_inst.example_audio
    form = FillInTheBlankForm()
    return render(
        request,
        'ruskeyverbs/fill_in_the_blank.html',
        context={'quiz_text': russian_text, 'answer': answer, 'form': form,
                 'pk': pk, 'file': example_audio_file}
    )


@login_required
def FillInTheBlankEval(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    verb_inst = example_inst.verb
    russian_text_list = strip_punct_lower(example_inst.russian_text)
    russian_text_list = russian_text_list.split()
    for i in range(len(russian_text_list)):
        if russian_text_list[i] in verb_inst.get_forms_list():
            answer = russian_text_list[i]
    if request.method == 'POST':
        form = FillInTheBlankForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['verb_part_of_speech']
            score = fuzz.ratio(user_input, answer)
            request.session['current_score'] = [score]
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'russian_text': example_inst.russian_text,
                                   'english_text': example_inst.translation_text,
                                   'answer': answer,
                                   'user_input': user_input,
                                   'score': score,
                                   'pk': pk})
        else:
            messages.warning(request,
                             """Something went wrong.
                             You did not enter a valid answer.""")
            return HttpResponseRedirect(reverse('fill-in-the-blank',
                                                args=[pk]))
    else:
        raise Http404


@login_required
def ArrangeWords(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text)
    russian_text_list = russian_text_list.split()
    shuffle(russian_text_list)
    tuple_list = []
    for i in range(len(russian_text_list)):
        tuple_list.append((i, russian_text_list[i]))
    form = ArrangeWordsForm(tuple_list)
    return render(request,
                  'ruskeyverbs/arrange_words.html',
                  context={'russian_text': example_inst.russian_text,
                           'english_text': example_inst.translation_text,
                           'form': form,
                           'pk': pk})


@login_required
def ArrangeWordsEval(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    if request.method == 'POST':
        form = ArrangeWordsForm(request.POST)
        if form.is_valid():
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'russian_text_list': russian_text_list,
                                   'pk':pk})
        else:
            print('wuh oh')
