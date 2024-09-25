from django.urls import path
from . import views

urlpatterns = [
    path('<int:league_id>/index/', views.index, name='index'),
    path('<int:league_id>/matchups/', views.matchups, name='matchups')
]
