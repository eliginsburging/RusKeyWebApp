from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('verbs/', views.VerbListPerUser, name='my-verbs'),
    path('verb/<int:pk>', views.VerbDetails.as_view(), name='verb-details'),
    path('accounts/', include('django.contrib.auth.urls')),
]
