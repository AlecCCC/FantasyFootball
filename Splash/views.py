import requests
from django.shortcuts import render
from django.http import JsonResponse
import json  # Import the json module



def splash_view(request):
    return render(request, 'splash.html')

