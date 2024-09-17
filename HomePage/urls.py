from django.urls import path
from . import views

urlpatterns = [
    path('league-info/<str:league_id>/', views.index, name='league-info'),
]
