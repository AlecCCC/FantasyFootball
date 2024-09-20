from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('matchups/', views.matchups, name='matchups')
]
