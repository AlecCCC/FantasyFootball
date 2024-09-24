import requests
from django.shortcuts import render

import requests
from django.shortcuts import render


def splash_view(request):
    username = ''
    user_id = ''

    if request.method == 'POST':
        username = request.POST.get('username')
        user_response = requests.get(f'https://api.sleeper.app/v1/user/{username}')

        if user_response.status_code == 200:
            user_data = user_response.json()
            user_id = user_data.get('user_id')
            leagues_response = requests.get(f'https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2024')

            if leagues_response.status_code == 200:
                leagues_data = leagues_response.json()


                for league in leagues_data:
                    avatar_id = league.get('avatar')
                    if avatar_id:

                        league['avatar_url'] = f"https://sleepercdn.com/avatars/{avatar_id}"
                    else:
                        league['avatar_url'] = None
                print(f'Username {username} User ID {user_id}')
                context = {
                    'username': username,
                    'user_id': user_id,
                    'leagues': leagues_data
                }

                return render(request, 'splash.html', context)
            else:
                # Handle case where leagues API request fails
                return render(request, 'splash.html', {'error': 'Failed to fetch leagues'})
        else:
            # Handle case where user API request fails
            return render(request, 'splash.html', {'error': 'Failed to fetch user'})

    context = {
    }
    return render(request, 'splash.html', context)