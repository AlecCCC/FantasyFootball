import requests
from django.shortcuts import render
from django.http import JsonResponse
import json  # Import the json module

# views.py in Splash app
import requests
from django.shortcuts import render
from django.http import JsonResponse


def splash_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        user_response = requests.get(f'https://api.sleeper.app/v1/user/{username}')

        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data.get('user_id')
            leagues_response = requests.get(f'https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2024')

            if leagues_response.status_code == 200:
                leagues_data = leagues_response.json()
                return render(request, 'splash.html', {'leagues': leagues_data})
            else:
                # Handle case where leagues API request fails
                return render(request, 'splash.html', {'error': 'Failed to fetch leagues'})
        else:
            # Handle case where user API request fails
            return render(request, 'splash.html', {'error': 'Failed to fetch user'})

    return render(request, 'splash.html')

