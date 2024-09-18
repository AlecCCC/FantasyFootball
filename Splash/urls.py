from django.urls import path
from . import views

urlpatterns = [
    path('', views.splash_view, name='splash'),
]