from datetime import datetime

import requests
from django.shortcuts import render

import requests
from django.shortcuts import render

import requests
from datetime import datetime
from django.shortcuts import render


def splash_view(request):

    now = datetime.now()
    year = 0


    if now.month >= 9:
        year = now.year
    else:
        year = now.year -1

    if request.method == 'POST':
        username = request.POST.get('username')
        user_response = requests.get(f'https://api.sleeper.app/v1/user/{username}')

        if user_response.status_code == 200:
            try:
                user_data = user_response.json()
                if user_data and isinstance(user_data, dict):
                    user_id = user_data.get('user_id')
                else:
                    return render(request, 'splash.html', {'error': 'Invalid user data received'})

                leagues_response = requests.get(f'https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{year}')
                if leagues_response.status_code == 200:
                    leagues_data = leagues_response.json()

                    # Check if leagues_data is empty and set a message
                    if not leagues_data:
                        return render(request, 'splash.html', {'error': 'No leagues found for this user'})

                    # Process league avatars
                    for league in leagues_data:
                        avatar_id = league.get('avatar')
                        league['avatar_url'] = f"https://sleepercdn.com/avatars/{avatar_id}" if avatar_id else None

                    context = {
                        'username': username,
                        'user_id': user_id,
                        'leagues': leagues_data
                    }
                    return render(request, 'splash.html', context)
                else:
                    return render(request, 'splash.html', {'error': 'Failed to fetch leagues'})
            except ValueError:
                return render(request, 'splash.html', {'error': 'Failed to parse user data'})
        else:
            return render(request, 'splash.html', {'error': 'Failed to fetch user'})

    return render(request, 'splash.html', {})