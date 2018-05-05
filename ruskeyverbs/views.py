from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.db.models import Min
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import UserSerializer
from fuzzywuzzy import fuzz
from random import shuffle, choices
from .models import Verb, Example, PerformancePerExample
from .tokens import account_activation_token
from .forms import FillInTheBlankForm, ArrangeWordsForm, ReproduceSentenceForm, MultipleChoiceForm, UserForm
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


def SignUp(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate Your RusKey Account'
            message = render_to_string('ruskeyverbs/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return render(request, 'ruskeyverbs/registration_landing.html', {
                'user': user,
                'email': user.email
            })
    else:
        form = UserForm()
    return render(request, 'ruskeyverbs/signup.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.ObjectDoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'ruskeyverbs/activation.html', {
            'success': True
        })
    else:
        return render(request, 'ruskeyverbs/activation.html', {
            'success': False
        })


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
    if PerformancePerExample.objects.filter(pk=example_pk,
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
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    if request.session['quiz_state'] != 1:
        raise Http404
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
    num_verbs = Verb.objects.count()
    if int(example_inst.verb.pk) == 1:
        rand_range = list(range(2, num_verbs + 1))
    elif int(example_inst.verb.pk) == num_verbs:
        rand_range = list(range(1, num_verbs))
    else:
        rand_range = (list(range(1, example_inst.verb.pk))
                      + list(range(example_inst.verb.pk + 1, num_verbs + 1)))
    choice_pks += choices(rand_range, k=3)
    shuffle(choice_pks)
    request.session['mcchoices'] = choice_pks
    request.session['target_field'] = target_field.name
    choice_list = []  # list of tuples that will be passed to the form
    # grab the right verb form for the other verbs
    verb_choices = Verb.objects.filter(pk__in=choice_pks)
    for verb_inst in verb_choices:
        verb_choice = getattr(verb_inst, target_field.name).replace(
            stress_mark, '')
        choice_list.append((verb_choice, verb_choice))
    quiz_text = example_inst.russian_text.replace(stressed_answer,
                                                  '___________')
    quiz_text = quiz_text.replace(stressed_answer.capitalize(),
                                  '____________')
    if 'progress' not in request.session:
        request.session['progress'] = 0
    form = MultipleChoiceForm(choice_list)
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
    if request.method != 'POST':
        raise Http404
    for word in russian_text_list:
        if word in example_inst.verb.get_forms_list(stressed=False):
            answer = word
    tuple_list = []
    target_field = request.session['target_field']
    verb_choices = Verb.objects.filter(pk__in=request.session['mcchoices'])
    for verb_inst in verb_choices:
        verb_choice = getattr(verb_inst, target_field).replace(
            stress_mark, '')
        tuple_list.append((verb_choice, verb_choice))
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
            """
            the current_score session variable will be used to determine the
            average score after all three quiz types have been completed for
            the given example; this average score is what is written to the DB
            """
            request.session['current_score'] = [score]
            # increment the progress bar if mid-quiz; initialize it otherwise
            try:
                request.session['progress'] += round(1/12, 3)*100
            except KeyError:
                request.session['progress'] = round(1/12, 3)*100
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


@login_required
def FillInTheBlank(request, pk):
    """
    view for fill inthe blank style quiz
    """
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    if request.session['quiz_state'] != 2:
        raise Http404
    example_inst = get_object_or_404(Example, pk=pk)
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    """
    test each word of the sentence to see which one is a form of the verb
    being studied
    """
    for word in russian_text_list:
        if word in example_inst.verb.get_forms_list():
            stressed_answer = word
    # replace that form with a blank
    russian_text = example_inst.russian_text.replace(stressed_answer,
                                                     '_________')
    russian_text = russian_text.replace(stressed_answer.capitalize(),
                                        '_________')
    form = FillInTheBlankForm()
    return render(
        request,
        'ruskeyverbs/fill_in_the_blank.html',
        context={'quiz_text': russian_text,
                 'form': form,
                 'pk': pk,
                 'file': example_inst.example_audio,
                 'english_text': example_inst.translation_text}
    )


@login_required
def FillInTheBlankEval(request, pk):
    """
    evaluation view for the fill in the blank quiz
    """
    if request.method != 'POST':
        raise Http404
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
    for word in russian_text_list:
        if word in example_inst.verb.get_forms_list(stressed=False):
            answer = word
    if request.method == 'POST':
        form = FillInTheBlankForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data['verb_part_of_speech']
            """
            do a fuzzy string comparison of the user's input to the expected
            answer identified above
            """
            score = fuzz.ratio(user_input, answer)
            request.session['current_score'].append(score)
            # increment the progress bar if mid-quiz; initialize it otherwise
            request.session['progress'] += round(1/12, 3)*100
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


@login_required
def ArrangeWords(request, pk):
    """
    quiz view for the arrange words type quiz
    """
    try:
        request.session['quiz_state'] += 1
        request.session.modified = True
    except KeyError:
        request.session['quiz_state'] = 0
    if request.session['quiz_state'] != 3:
        raise Http404
    example_inst = get_object_or_404(Example, pk=pk)
    """
    create a randomized list of the words in the sentence, which will be the
    options for the choice fields in the arrange words form
    """
    randomized_russian_text_list = strip_punct_lower(
        example_inst.russian_text).split()
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
    for word in randomized_russian_text_list:
        tuple_list.append((word, word))
    form = ArrangeWordsForm(tuple_list, sentence_len)
    return render(request,
                  'ruskeyverbs/arrange_words.html',
                  context={'russian_text': example_inst.russian_text,
                           'english_text': example_inst.translation_text,
                           'form': form,
                           'pk': pk,
                           'file': example_inst.example_audio})


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
    if request.method != 'POST':
        raise Http404
    russian_text_list = strip_punct_lower(example_inst.russian_text,
                                          stressed=True).split()
    russian_text_list_no_stress = strip_punct_lower(
        example_inst.russian_text).split()
    tuple_list = []
    for verb_form in request.session['extra_options']:
        tuple_list.append((verb_form, verb_form))
    for word in russian_text_list:
        unstressed_word = word.replace(stress_mark, '')
        tuple_list.append((unstressed_word, unstressed_word))
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
            request.session['progress'] += round(1/12, 3)*100
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
    if request.method != 'POST':
        raise Http404
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
            request.session['progress'] += round(1/12, 3)*100
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
            if not PerformancePerExample.objects.filter(example=example_inst,
                                                        user=request.user).exists():
                PerformanceObj = PerformancePerExample(
                    example=example_inst,
                    user=request.user,
                    easiness_factor=2.5,
                    last_interval=1,
                    date_last_studied=datetime.date.today(),
                    due_date=datetime.date.today()
                    )
            else:
                PerformanceObj = PerformancePerExample.objects.get(example=example_inst,
                                                           user=request.user)
            PerformanceObj.update_interval(average_score)

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
            if PerformancePerExample.objects.filter(pk=pk,
                                                    user=request.user).exists():

                not_studied = False
            else:
                not_studied = True
            try:
                request.session['quiz_counter'] += 1
            except KeyError:
                request.session['quiz_counter'] = 1
            if request.session['quiz_counter'] >= 3:
                request.session['quiz_state'] += 1
            else:
                request.session['quiz_state'] = 0
            print(request.session['quiz_state'], request.session['quiz_counter'])
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


@login_required
def QuizSummary(request, pk):
    verb_inst = get_object_or_404(Verb, pk=pk)
    if request.session['quiz_state'] == 5:
        return render(request,
                      'ruskeyverbs/quiz_summary.html',
                      context={'verb': verb_inst, 'pk': pk})
    else:
        raise Http404


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows User instances to be viewed
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    def get_queryset(self):
        queryset = User.objects.all()
        filter_value = self.request.query_params.get('username', None)
        if filter_value is not None:
            queryset =queryset.filter(username=filter_value)
        return queryset
