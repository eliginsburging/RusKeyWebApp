from django.urls import path, include

from . import views

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
    path('accounts/', include('django.contrib.auth.urls')),
]
