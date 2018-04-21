from itertools import chain
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import generic
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Min
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core import serializers
from fuzzywuzzy import fuzz
from random import shuffle, randint
from .models import Verb, Example, PerformancePerExample
from .forms import FillInTheBlankForm, ArrangeWordsForm, ReproduceSentenceForm, MultipleChoiceForm
import datetime
import decimal
import re

stress_mark = chr(769)


def strip_punct_lower(some_string, stressed=False):
    """
    helper function that takes a string and returns the same string in lower
    case with all punctuation marks stripped
    """
    regular_exp = '[,.?!;:]*'
    if not stressed:
        regular_exp += stress_mark + '*'
    punctuation = re.compile(regular_exp)
    return punctuation.sub('', some_string).lower()


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
    """
    list view for verbs available in the system. Sorts by due date
    (if studied previously) then frequency ranking
    """
    # two query sets because otherwise unstudied verbs would display before
    # studied ones
    verbs_with_due_dates = Verb.objects.annotate(
        due=Min(
            'example__performanceperexample__due_date',
            filter=Q(
                example__performanceperexample__user_id=request.user.pk)
            )
        ).order_by(F('due').asc(nulls_last=True))
    sorted_verb_list = list(verbs_with_due_dates)
    return render(
        request,
        'ruskeyverbs/list_view_per_user.html',
        context={'verb_list': sorted_verb_list}
    )


@login_required
def VerbDetails(request, pk):
    """
    detail view for verbs; page will display conjugation and example info/audio
    for user
    """
    verb = Verb.objects.get(pk=pk)
    example_pk = Example.objects.annotate(
        due=Min('performanceperexample__due_date',
                filter=Q(
                    performanceperexample__user_id=request.user.pk)
                )
        ).filter(verb=verb).order_by('due')[0].pk
    """
    If the user has previously studied the example, send them right
    into the quiz; otherwise, send them to the study page before the
    quiz
    """
    if not PerformancePerExample.objects.filter(pk=example_pk,
                                                user=request.user).exists():
        not_studied = False
    else:
        not_studied = True

    request.session['quiz_counter'] = 0
    # quiz_coutner will determine when the user is bumped out of the quiz loop
    request.session['progress'] = 0
    # progress is used to fill in the progress bar
    request.session['quiz_summary'] = []
    """quiz_summary will contain tuples of information on quiz performance
    (Russian_Sentence, Translation_Text, Quiz_1_Score, Quiz_2_Score,
    Quiz_3_score, Average_Score )"""
    request.session['quiz_state'] = 0
    # quiz state will restrict the user to going through the quizzes in order
    return render(
        request,
        'ruskeyverbs/verb_detail.html',
        context={'verb': verb,
                 'example_pk': example_pk,
                 'not_studied': not_studied}
    )


@login_required
def StudyPage(request, pk):
    """
    page will be displayed before quiz if the user has not yet studied a verb
    """
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    """
    test each word of the sentence to see which one is a form of the verb
    being studied and determine which form it is
    """
    for word in russian_text_list:
        if word in example_inst.verb.get_forms_list(stressed=True):
            target_verb = word
            target_verb_modified = "<b>" + word + "</b>"
    russian_text_bold = example_inst.russian_text.replace(target_verb,
                                                     target_verb_modified)
    request.session['quiz-state'] = 0
    return render(
        request,
        'ruskeyverbs/study_session.html',
        context={
            'russian_text': russian_text_bold,
            'english_text': example_inst.translation_text,
            'pk': pk,
            'file': example_inst.example_audio,
        }
            )


@login_required
def MultipleChoice(request, pk):
    """
    view for multiple choice quiz
    """
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    """
    test each word of the sentence to see which one is a form of the verb
    being studied and determine which form it is
    """
    field_names = Verb._meta.get_fields()
    for word in russian_text_list:
        for field in field_names:
            try:
                verb_form = getattr(example_inst.verb, field.name)
                if verb_form == word:
                    target_field = field
                    answer = word.replace(stress_mark, '')
                    stressed_answer = word
            except AttributeError:
                pass
                # pass to get around many to one field returned by get_fields()
    # create a list of the pks of 3 other random verbs and randomize it
    choice_pks = [int(example_inst.verb.pk)]
    while len(choice_pks) < 4:
        random_pk = randint(1, Verb.objects.count())
        while random_pk in choice_pks:
            random_pk = randint(1, Verb.objects.count())
        choice_pks.append(random_pk)
    shuffle(choice_pks)
    request.session['mcchoices'] = choice_pks
    request.session['target_field'] = target_field.name
    choice_list = []  # list of tuples that will be passed to the form
    # grab the right verb form for the other verbs
    for i in choice_pks:
        choice_list.append(
            (getattr(Verb.objects.get(pk=i), target_field.name).replace(
                chr(769), ''),
             getattr(Verb.objects.get(pk=i), target_field.name).replace(
                 chr(769), ''))
            )
    quiz_text = example_inst.russian_text.replace(stressed_answer,
                                                  '___________')
    quiz_text = quiz_text.replace(stressed_answer.capitalize(),
                                  '____________')
    try:
        print(request.session['progress'])
    except KeyError:
        request.session['progress'] = 0
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    form = MultipleChoiceForm(choice_list)
    if request.session['quiz_state'] == 1:
        return render(
            request,
            'ruskeyverbs/multiple_choice.html',
            context={
                'quiz_text': quiz_text,
                'form': form,
                'pk': pk,
                'file': example_inst.example_audio,
                'english_text': example_inst.translation_text
            }
            )
    else:
        raise Http404


@login_required
def MultipleChoiceEval(request, pk):
    """
    evaluation view for multiple choice fill in the blank
    """
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=False).split()
    """
    test each word of the sentence to see which one is a form of the verb
    being studied - this is the correct answer to the quiz
    """
    for i in range(len(russian_text_list)):
        if russian_text_list[i] in example_inst.verb.get_forms_list(stressed=False):
            answer = russian_text_list[i]
    tuple_list = []
    target_field = request.session['target_field']
    for i in request.session['mcchoices']:
        tuple_list.append(
            (getattr(Verb.objects.get(pk=i), target_field).replace(
                chr(769), ''),
             getattr(Verb.objects.get(pk=i), target_field).replace(
                 chr(769), ''))
            )
    tuple_list.append((answer, answer))
    if request.method == 'POST':
        form = MultipleChoiceForm(tuple_list, request.POST)
        if form.is_valid():
            if form.cleaned_data['answer'] == answer:
                # if the lists match exactly, the score is 100
                score = 100
            else:
                score = 0
            user_input = form.cleaned_data['answer']
            request.session['current_score'].append(score)
            # increment the progress bar if mid-quiz; initialize it otherwise
            try:
                request.session['progress'] += round(1/16, 3)*100
            except KeyError:
                request.session['progress'] = round(1/16, 3)*100
            request.session.modified = True
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'pk': pk,
                                   'score': score,
                                   'user_input': user_input,
                                   'answer': example_inst.russian_text,
                                   'russian_text': example_inst.russian_text,
                                   'quiz_state': 1})
        else:
            print(form.errors)
            messages.warning(request,
                             """Something went wrong.
                             You did not enter a valid answer.""")
            return HttpResponseRedirect(reverse('multiple-choice',
                                                args=[pk]))
    else:
        raise Http404


@login_required
def FillInTheBlank(request, pk):
    """
    view for fill inthe blank style quiz
    """
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    """
    test each word of the sentence to see which one is a form of the verb
    being studied
    """
    for i in range(len(russian_text_list)):
        if russian_text_list[i] in example_inst.verb.get_forms_list():
            stressed_answer = russian_text_list[i]
    # replace that form with a blank
    russian_text = example_inst.russian_text.replace(stressed_answer,
                                                     '_________')
    russian_text = russian_text.replace(stressed_answer.capitalize(),
                                        '_________')
    form = FillInTheBlankForm()
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    if request.session['quiz_state'] == 2:
        return render(
            request,
            'ruskeyverbs/fill_in_the_blank.html',
            context={'quiz_text': russian_text,
                     'form': form,
                     'pk': pk,
                     'file': example_inst.example_audio,
                     'english_text': example_inst.translation_text}
        )
    else:
        raise Http404


@login_required
def FillInTheBlankEval(request, pk):
    """
    evaluation view for the fill in the blank quiz
    """
    example_inst = get_object_or_404(Example, pk=pk)
    """
    since the user is unable to type stress marks, we omit them in identifying
    the correct answer (the form which was omitted in the FillInTheBlank view)
    """
    russian_text_list = strip_punct_lower(example_inst.russian_text).split()
    """
    test each word of the sentence to see which one is a form of the verb
    being studied - this is the correct answer to the quiz
    """
    for i in range(len(russian_text_list)):
        if russian_text_list[i] in example_inst.verb.get_forms_list(stressed=False):
            answer = russian_text_list[i]
    if request.method == 'POST':
        form = FillInTheBlankForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['verb_part_of_speech']
            """
            do a fuzzy string comparison of the user's input to the expected
            answer identified above
            """
            score = fuzz.ratio(user_input, answer)
            """
            the current_score session variable will be used to determine the
            average score after all three quiz types have been completed for
            the given example; this average score is what is written to the DB
            """
            request.session['current_score'] = [score]
            # increment the progress bar if mid-quiz; initialize it otherwise
            request.session['progress'] += round(1/16, 3)*100
            request.session.modified = True
            """
            quiz_state context variable below determines where the user is
            directed next
            """
            return render(
                request,
                'ruskeyverbs/answer_evaluation.html',
                context={'russian_text': example_inst.russian_text,
                         'english_text': example_inst.translation_text,
                         'answer': answer,
                         'user_input': user_input,
                         'score': score,
                         'pk': pk,
                         'quiz_state': 2})
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
    """
    quiz view for the arrange words type quiz
    """
    example_inst = get_object_or_404(Example, pk=pk)
    """
    create a randomized list of the words in the sentence, which will be the
    options for the choice fields in the arrange words form
    """
    randomized_russian_text_list = strip_punct_lower(example_inst.russian_text).split()
    sentence_len = len(randomized_russian_text_list)
    """
    add three other random forms the verb under quiz (that are not already in
    the sentence) to the list
    """
    randomized_verb_forms = example_inst.verb.get_forms_list(stressed=False,
                                                             random=True)
    shuffle(randomized_verb_forms)
    count = 0
    for verb_form in randomized_verb_forms:
        if verb_form not in randomized_russian_text_list:
            randomized_russian_text_list.append(verb_form)
            count += 1
        if count >= 3:
            break
    request.session['extra_options'] = randomized_russian_text_list
    # create a list of tuples that will be the choices for the choice fields
    shuffle(randomized_russian_text_list)
    tuple_list = []
    for i in range(len(randomized_russian_text_list)):
        tuple_list.append((randomized_russian_text_list[i],
                           randomized_russian_text_list[i]))
    form = ArrangeWordsForm(tuple_list, sentence_len)
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    if request.session['quiz_state'] == 3:
        return render(request,
                      'ruskeyverbs/arrange_words.html',
                      context={'russian_text': example_inst.russian_text,
                               'english_text': example_inst.translation_text,
                               'form': form,
                               'pk': pk,
                               'file': example_inst.example_audio})
    else:
        raise Http404


@login_required
def ArrangeWordsEval(request, pk):
    """
    eval view for arrange words quiz
    """
    example_inst = get_object_or_404(Example, pk=pk)
    """
    create a list of the words in the sentence, which will be used
    to bind the form
    """
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    russian_text_list_no_stress = strip_punct_lower(
        example_inst.russian_text).split()
    tuple_list = []
    for verb_form in request.session['extra_options']:
        tuple_list.append((verb_form, verb_form))
    for i in range(len(russian_text_list)):
        tuple_list.append((russian_text_list_no_stress[i],
                           russian_text_list_no_stress[i]))
    sentence_len = len(russian_text_list)
    if request.method == 'POST':
        form = ArrangeWordsForm(tuple_list, sentence_len, request.POST)
        if form.is_valid():
            if form.cleaned_data.values() == russian_text_list_no_stress:
                # if the lists match exactly, the score is 100
                score = 100
            else:
                # otherwise do fuzzy string comparison #
                user_input_string = ''.join(form.cleaned_data.values())
                answer = ''.join(russian_text_list_no_stress)
                score = fuzz.ratio(user_input_string, answer)
            user_input = ' '.join(form.cleaned_data.values())
            request.session['current_score'].append(score)
            request.session['progress'] += round(1/16, 3)*100
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'pk': pk,
                                   'score': score,
                                   'user_input': user_input,
                                   'answer': example_inst.russian_text,
                                   'russian_text': example_inst.russian_text,
                                   'quiz_state': 3})
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
    """
    reproduce sentence quiz view
    """
    example_inst = get_object_or_404(Example, pk=pk)
    form = ReproduceSentenceForm()
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    if request.session['quiz_state'] == 4:
        return render(request, 'ruskeyverbs/reproduce_sentence.html',
                      context={'english_text': example_inst.translation_text,
                               'form': form,
                               'pk': pk,
                               'file': example_inst.example_audio})
    else:
        raise Http404


@login_required
def ReproduceSentenceEval(request, pk):
    example_inst = get_object_or_404(Example, pk=pk)
    verb_pk = example_inst.verb.pk
    verb = example_inst.verb
    if request.method == 'POST':
        form = ReproduceSentenceForm(request.POST)
        if form.is_valid():
            # fuzzy string comparison to examine the accuracy of user input
            user_input = strip_punct_lower(form.cleaned_data['sentence_field'])
            answer = strip_punct_lower(example_inst.russian_text)
            score = fuzz.ratio(user_input, answer)
            request.session['current_score'].append(score)
            request.session['progress'] += round(1/16, 3)*100
            if request.session['progress'] > 95:
                request.session['progress'] = 100
            """
            calculate the average score from the session list (this is what
            gets written to the PerformancePerExample model)
            """
            average_score = sum(
                request.session['current_score'])/len(
                    request.session['current_score'])
            average_score = round(average_score, 2)
            average_score /= 100
            try:
                request.session['quiz_summary'].append(
                    (
                        example_inst.russian_text,
                        example_inst.translation_text,
                        request.session['current_score'][0],
                        request.session['current_score'][1],
                        request.session['current_score'][2],
                        score,
                        int(average_score * 100)
                    )

                )
            except KeyError:
                request.session['quiz_summary'] = []
            request.session.modified = True
            """
            test whether the user already has a PerformancePerExample for
            this verb
            """
            try:
                PerformanceObj = PerformancePerExample.objects.get(
                    example=example_inst, user=request.user)
                last_interval = PerformanceObj.last_interval
                easiness_factor = PerformanceObj.easiness_factor
                """ if not, set default values; note that PerformanceObj is set to
                None for the purposes of a conditional
                """
            except ObjectDoesNotExist:
                PerformanceObj = None
                last_interval = 1
                easiness_factor = 2.5
            # if the user really messed up, set next study date to 1 day out
            if average_score*5 < 3.5:
                last_interval = 1
                """ otherwise set/update last_interval, easiness_factor in accordance with
                the supermemo2 algorithm"""
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
            # if the user has a PerformancePerExample for this example, update it
            if PerformanceObj:
                PerformanceObj.easiness_factor = easiness_factor
                PerformanceObj.last_interval = last_interval
                PerformanceObj.date_last_studied = datetime.date.today()
                PerformanceObj.due_date = (datetime.date.today()
                                           + datetime.timedelta(
                                               days=last_interval))
                PerformanceObj.save()
            # otherwise create one
            else:
                PerformanceObj = PerformancePerExample(example=example_inst,
                                                       user=request.user,
                                                       easiness_factor=easiness_factor,
                                                       last_interval=last_interval,
                                                       date_last_studied=datetime.date.today(),
                                                       due_date=(datetime.date.today()
                                                                 + datetime.timedelta(days=last_interval)))
                PerformanceObj.save()
            # after update, determine which example is due next
            pk = Example.objects.annotate(
                due=Min('performanceperexample__due_date',
                        filter=Q(
                            performanceperexample__user_id=request.user.pk)
                        )
                ).filter(verb=verb).order_by('due')[0].pk
            """
            If the user has previously studied the next example, send them right
            into the quiz; otherwise, send them to the study page before the
            quiz
            """
            try:
                print(PerformancePerExample.objects.get(pk=pk,
                                                        user=request.user))
                not_studied = False
            except ObjectDoesNotExist:
                not_studied = True
            try:
                request.session['quiz_counter'] += 1
            except KeyError:
                request.session['quiz_counter'] = 1
            if request.session['quiz_counter'] >= 4:
                request.session['quiz_state'] += 1
            else:
                request.session['quiz_state'] = 0
            request.session.modified = True
            return render(request,
                          'ruskeyverbs/answer_evaluation.html',
                          context={'pk': pk,
                                   'score': score,
                                   'user_input': user_input,
                                   'answer': answer,
                                   'russian_text': example_inst.russian_text,
                                   'quiz_state': 4,
                                   'verb_pk': verb_pk,
                                   'not_studied': not_studied})
        else:
            messages.warning(request,
                             """Something went wrong.
                             You did not enter a valid answer.""")
            return HttpResponseRedirect(reverse('arrange-words',
                                                args=[pk]))
    else:
        raise Http404


@login_required
def QuizSummary(request, pk):
    verb_inst = get_object_or_404(Verb, pk=pk)
    if request.session['quiz_state'] == 5:
        return render(request,
                      'ruskeyverbs/quiz_summary.html',
                      context={'verb': verb_inst, 'pk': pk})
    else:
        raise Http404
