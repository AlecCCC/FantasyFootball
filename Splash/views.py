from datetime import datetime
import requests
from django.shortcuts import render


def splash_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        year_input = request.POST.get('year')

        try:
            year = int(year_input)
        except (TypeError, ValueError):
            now = datetime.now()
            year = now.year if now.month >= 9 else now.year - 1

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

                    if not leagues_data:
                        return render(request, 'splash.html', {'error': f'No leagues found for {year}'})

                    for league in leagues_data:
                        avatar_id = league.get('avatar')
                        league['avatar_url'] = f"https://sleepercdn.com/avatars/{avatar_id}" if avatar_id else None

                    context = {
                        'username': username,
                        'user_id': user_id,
                        'leagues': leagues_data,
                        'year': year
                    }
                    return render(request, 'splash.html', context)
                else:
                    return render(request, 'splash.html', {'error': f'Failed to fetch leagues for {year}'})
            except ValueError:
                return render(request, 'splash.html', {'error': 'Failed to parse user data'})
        else:
            return render(request, 'splash.html', {'error': 'Failed to fetch user'})

    return render(request, 'splash.html', {})
