from django.contrib.auth import views as auth_views
from . import views
from django.urls import path, include
from django.conf import settings
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('', views.index, name='index'),
    path('verbs/', views.VerbListPerUser, name='my-verbs'),
    path('verb/<int:pk>', views.VerbDetails, name='verb-details'),
    path('example/<int:pk>/study', views.StudyPage,
         name='study-session'),
    path('example/<int:pk>/mcquiz', views.MultipleChoice,
         name='multiple-choice'),
    path('example/<int:pk>/mcquiz/eval', views.MultipleChoiceEval,
         name='multiple-choice-eval'),
    path('example/<int:pk>/fitbquiz', views.FillInTheBlank,
         name='fill-in-the-blank'),
    path('example/<int:pk>/fitbquiz/eval', views.FillInTheBlankEval,
         name='fill-in-eval'),
    path('example/<int:pk>/arrangequiz', views.ArrangeWords,
         name='arrange-words'),
    path('example/<int:pk>/arrangequiz/eval', views.ArrangeWordsEval,
         name='arrange-words-eval'),
    path('example/<int:pk>/reproducequiz', views.ReproduceSentence,
         name='reproduce-sentence'),
    path('example/<int:pk>/reproducequiz/eval', views.ReproduceSentenceEval,
         name='reproduce-sentence-eval'),
    path('verb/<int:pk>/quizsummary', views.QuizSummary,
         name='quiz-summary'),
    path('accounts/login/', auth_views.login,
         {'template_name': 'ruskeyverbs/login.html'}, name='login'),
    path('accounts/logout/', auth_views.logout,
         {'template_name': 'ruskeyverbs/logout.html'}, name='logout'),
    path('register/', views.SignUp, name='signup'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('userapi/<uname>/', views.get_user, name='get-user'),
]
