from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('submit-league-id/', views.submit_league_id, name='submit-league-id'),  # URL for submitting the league ID

]