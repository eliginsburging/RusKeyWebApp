from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('verbs/', views.VerbListPerUser, name='my-verbs'),
    path('verb/<int:pk>', views.VerbDetails.as_view(), name='verb-details'),
    path('example/<int:pk>/fitbquiz', views.FillInTheBlank,
         name='fill-in-the-blank'),
    path('example/<int:pk>/fitbquiz/eval', views.FillInTheBlankEval,
         name='fill-in-eval'),
    path('example/<int:pk>/arrangequiz', views.ArrangeWords,
         name='arrange-words'),
    path('example/<int:pk>/arrangequiz/eval', views.ArrangeWordsEval,
         name='arrange-words-eval'),
    path('accounts/', include('django.contrib.auth.urls')),
]
