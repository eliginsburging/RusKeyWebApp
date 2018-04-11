from itertools import chain
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from fuzzywuzzy import fuzz
from random import shuffle
from .models import Verb, Example, PerformancePerExample
from .forms import FillInTheBlankForm, ArrangeWordsForm, ReproduceSentenceForm
import datetime
import decimal

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
    verbs_with_due_dates = Verb.objects.annotate(
        due=Min(
            'example__performanceperexample__due_date',
            filter=Q(
                example__performanceperexample__user_id=request.user.pk)
            )
        ).order_by('due').exclude(due=None)
    verbs_without_due_dates = Verb.objects.annotate(
        due=Min('example__performanceperexample__due_date',
                filter=Q(
                    example__performanceperexample__user_id=request.user.pk)
                )
        ).exclude(~Q(due=None))
    sorted_verb_list = list(chain(verbs_with_due_dates,
                                  verbs_without_due_dates))
    current_user = request.user
    return render(
        request,
        'ruskeyverbs/list_view_per_user.html',
        context={'verb_list': sorted_verb_list}
    )


@login_required
def VerbDetails(request, pk):
    current_user = request.user
    verb = Verb.objects.get(pk=pk)
    example_pk = Example.objects.annotate(
        due=Min('performanceperexample__due_date',
                filter=Q(
                    performanceperexample__user_id=request.user.pk)
                )
        ).filter(verb=verb).order_by('due')[0].pk
    request.session['quiz_counter'] = 0
    return render(
        request,
        'ruskeyverbs/verb_detail.html',
        context={'verb': verb, 'example_pk': example_pk}
    )


@login_required
def FillInTheBlank(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    verb_inst = example_inst.verb
    russian_text = example_inst.russian_text
    russian_text_list = strip_punct_lower(russian_text)
    russian_text_list = russian_text_list.split()
    russian_text_list_stressed = strip_punct_lower(russian_text,
                                                   stressed=True).split()
    for i in range(len(russian_text_list)):
        if russian_text_list[i] in verb_inst.get_forms_list():
            answer = russian_text_list[i]
            stressed_answer = russian_text_list_stressed[i]
    russian_text = russian_text.replace(stressed_answer, '_________')
    russian_text = russian_text.replace(stressed_answer.capitalize(),
                                        '_________')
    example_audio_file = example_inst.example_audio
    form = FillInTheBlankForm()
    try:
        request.session['quiz_counter'] += 1
    except KeyError:
        request.session['quiz_counter'] = 1
    return render(
        request,
        'ruskeyverbs/fill_in_the_blank.html',
        context={'quiz_text': russian_text,
                 'answer': answer,
                 'form': form,
                 'pk': pk,
                 'file': example_audio_file,
                 'english_text': example_inst.translation_text}
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
            return render(
                request,
                'ruskeyverbs/answer_evaluation.html',
                context={'russian_text': example_inst.russian_text,
                         'english_text': example_inst.translation_text,
                         'answer': answer,
                         'user_input': user_input,
                         'score': score,
                         'pk': pk,
                         'quiz_state': 1})
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
    randomized_russian_text_list = russian_text_list[:]
    shuffle(randomized_russian_text_list)
    tuple_list = []
    for i in range(len(russian_text_list)):
        tuple_list.append((randomized_russian_text_list[i],
                           randomized_russian_text_list[i]))
    form = ArrangeWordsForm(tuple_list)
    example_audio_file = example_inst.example_audio
    return render(request,
                  'ruskeyverbs/arrange_words.html',
                  context={'russian_text': example_inst.russian_text,
                           'english_text': example_inst.translation_text,
                           'form': form,
                           'pk': pk,
                           'file': example_audio_file})


@login_required
def ArrangeWordsEval(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    russian_text_list_no_stress = strip_punct_lower(
        example_inst.russian_text).split()
    tuple_list = []
    for i in range(len(russian_text_list)):
        tuple_list.append((russian_text_list_no_stress[i],
                           russian_text_list_no_stress[i]))
    print(tuple_list)
    if request.method == 'POST':
        form = ArrangeWordsForm(tuple_list, request.POST)
        if form.is_valid():
            if form.cleaned_data.values() == russian_text_list_no_stress:
                score = 100
            else:
                user_input_string = ''.join(form.cleaned_data.values())
                print(f"user input {user_input_string}")
                answer = ''.join(russian_text_list_no_stress)
                print(f'answer {answer}')
                score = fuzz.ratio(user_input_string, answer)
            user_input = ' '.join(form.cleaned_data.values())
            answer = example_inst.russian_text
            request.session['current_score'].append(score)
            request.session.modified = True
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'russian_text_list': russian_text_list,
                                   'pk': pk,
                                   'score': score,
                                   'user_input': user_input,
                                   'answer': answer,
                                   'russian_text': example_inst.russian_text,
                                   'quiz_state': 2})
        else:
            messages.warning(request,
                             """Something went wrong.
                             You did not enter a valid answer.""")
            return HttpResponseRedirect(reverse('arrange-words',
                                                args=[pk]))
    else:
        raise Http404


@login_required
def ReproduceSentence(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    form = ReproduceSentenceForm()
    example_audio_file = example_inst.example_audio
    return render(request, 'ruskeyverbs/reproduce_sentence.html',
                  context={'english_text': example_inst.translation_text,
                           'form': form,
                           'pk': pk,
                           'file': example_audio_file})


@login_required
def ReproduceSentenceEval(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    verb_pk = example_inst.verb.pk
    verb = example_inst.verb
    if request.method == 'POST':
        form = ReproduceSentenceForm(request.POST)
        if form.is_valid():
            user_input = strip_punct_lower(form.cleaned_data['sentence_field'])
            answer = strip_punct_lower(example_inst.russian_text)
            score = fuzz.ratio(user_input, answer)
            request.session['current_score'].append(score)
            request.session.modified = True
            average_score = sum(
                request.session['current_score'])/len(
                    request.session['current_score'])
            average_score /= 100
            average_score = int(average_score)
            try:
                PerformanceObj = PerformancePerExample.objects.get(
                    example=example_inst, user=request.user)
                last_interval = PerformanceObj.last_interval
                easiness_factor = PerformanceObj.easiness_factor
            except ObjectDoesNotExist:
                PerformanceObj = None
                last_interval = 1
                easiness_factor = 2.5
            if average_score*5 < 3.5:
                last_interval = 1
            else:
                if last_interval == 1:
                    last_interval = 2
                elif last_interval == 2:
                    last_interval = 6
                else:
                    easiness_factor += decimal.Decimal(0.1-(5-(average_score*5))*(0.08+(5-(average_score*5))*0.02))
                    if easiness_factor < 1.3:
                        easiness_factor = 1.3
                    elif easiness_factor > 5:
                        easiness_factor = 5
                    last_interval *= easiness_factor
                    last_interval = int(last_interval)
            if PerformanceObj:
                PerformanceObj.easiness_factor = easiness_factor
                PerformanceObj.last_interval = last_interval
                PerformanceObj.date_last_studied = datetime.date.today()
                PerformanceObj.due_date = (datetime.date.today()
                                           + datetime.timedelta(
                                               days=last_interval))
                PerformanceObj.save()
            else:
                PerformanceObj = PerformancePerExample(example=example_inst,
                                                       user=request.user,
                                                       easiness_factor=easiness_factor,
                                                       last_interval=last_interval,
                                                       date_last_studied=datetime.date.today(),
                                                       due_date=(datetime.date.today()
                                                                 + datetime.timedelta(days=last_interval)))
                PerformanceObj.save()
            print(request.session['current_score'])
            print(request.session['quiz_counter'])
            pk = Example.objects.annotate(
                due=Min('performanceperexample__due_date',
                        filter=Q(
                            performanceperexample__user_id=request.user.pk)
                        )
                ).filter(verb=verb).order_by('due')[0].pk
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'pk': pk,
                                   'score': score,
                                   'user_input': user_input,
                                   'answer': answer,
                                   'russian_text': example_inst.russian_text,
                                   'quiz_state': 3,
                                   'verb_pk': verb_pk})
        else:
            messages.warning(request,
                             """Something went wrong.
                             You did not enter a valid answer.""")
            return HttpResponseRedirect(reverse('arrange-words',
                                                args=[pk]))
    else:
        raise Http404
