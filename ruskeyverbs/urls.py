from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('verbs/', views.VerbListPerUser.as_view(), name='my-verbs'),
    path('accounts/', include('django.contrib.auth.urls')),
]
