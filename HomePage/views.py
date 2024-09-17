from django.shortcuts import render
import requests
import json
import os
from datetime import datetime, timedelta


# Create your views here.
def index(request, league_id=None):
    # Ensure a league_id is provided, either from the URL or session
    if not league_id:
        league_id = request.session.get('league_id')

    if not league_id:
        # Handle case where no league ID is provided
        return render(request, 'homepage/error.html', {'error': 'No League ID provided'})

    # API URLs and cache file
    API_URL = "https://api.sleeper.app/v1/players/nfl/"
    CACHE_FILE = "nfl_players_cache.json"
    CACHE_DURATION = timedelta(hours=6)  # Fetch new data if the cache is older than this

    get_rosters_in_league = f'https://api.sleeper.app/v1/league/{league_id}/rosters'
    get_users_in_league = f'https://api.sleeper.app/v1/league/{league_id}/users'
    get_weekly_matchups = f'https://api.sleeper.app/v1/league/{league_id}/matchups/2'
    get_league_info = f'https://api.sleeper.app/v1/league/{league_id}'

    rostered_players = []
    user_list = []
    roster_ids = []
    league_user_stats = {}

    def fetch_data_from_api():
        print("Fetching data from API...")
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            # Save the data to a local cache file
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
        else:
            response.raise_for_status()

    def load_data():
        if os.path.exists(CACHE_FILE):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
            if datetime.now() - file_mod_time < CACHE_DURATION:
                print("Loading data from cache...")
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
        # If no cache or cache is expired, fetch new data
        return fetch_data_from_api()

    nfl_data = load_data()

    print(f"Total players loaded: {len(nfl_data)}")

    # Get League Name
    response = requests.get(get_league_info).json()
    league_name = response['name']

    # Fetch roster data
    response = requests.get(get_rosters_in_league).json()

    # Loop through rosters and add owner and roster IDs
    for roster in response:
        roster_id = roster['roster_id']
        owner_id = roster['owner_id']

        league_user_stats = {
            'roster_id': roster_id,
            'owner_id': owner_id
        }
        roster_ids.append(league_user_stats)

    # Fetch users in the league
    response = requests.get(get_users_in_league).json()

    # Grab each user id, team_name, display_name
    for user in response:
        user_id = user['user_id']
        team_name = user['metadata'].get('team_name', 'No Team Name')
        display_name = user['display_name']
        user_avatar = user['avatar']

        league_user_stats = {
            'user_id': user_id,
            'team_name': team_name,
            'display_name': display_name,
            'avatar': user_avatar
        }
        user_list.append(league_user_stats)

    # Create a mapping of owner_id to roster_id
    roster_map = {item['owner_id']: item['roster_id'] for item in roster_ids}

    # Add roster_id to each user and initialize 'players' and 'starters'
    for user in user_list:
        user['roster_id'] = roster_map.get(user['user_id'])
        user['players'] = user.get('players', [])  # Ensure 'players' exists
        user['starters'] = user.get('starters', [])  # Ensure 'starters' exists

    # Fetch roster data again to populate players and starters
    response = requests.get(get_rosters_in_league).json()

    for roster in response:
        owner_id = roster['owner_id']

        for user_data in user_list:
            if user_data['user_id'] == owner_id:
                # Populate 'players' and 'starters'
                user_data['players'] = roster.get('players', [])
                user_data['starters'] = roster.get('starters', [])
                rostered_players.append(user_data['players'])  # Add rostered players
                break

    # Create a list of all rostered players
    rostered_players = [team.get('players', []) for team in user_list]

    #######################################

    # Load the cached player data
    with open('nfl_players_cache.json', 'r') as file:
        player_data = json.load(file)

    # Convert Player IDs to Player Name and get their position
    for user_data in user_list:
        user_data['players'] = user_data.get('players', [])  # Ensure 'players' is initialized
        updated_players = [
            {
                'full_name': player_data.get(player_id, {}).get('full_name', player_id),
                'position': player_data.get(player_id, {}).get('position', 'Unknown Position'),
                'player_id': player_data.get(player_id, {}).get('player_id', 'Unknown Player ID')
            }
            for player_id in user_data['players']
        ]
        user_data['players'] = updated_players

        user_data['starters'] = user_data.get('starters', [])  # Ensure 'starters' is initialized
        updated_starters = [
            {
                'full_name': player_data.get(player_id, {}).get('full_name', player_id),
                'position': player_data.get(player_id, {}).get('position', 'Unknown Position'),
                'player_id': player_data.get(player_id, {}).get('player_id', 'Unknown Player ID')
            }
            for player_id in user_data['starters']
        ]
        user_data['starters'] = updated_starters

    user_list = [user for user in user_list if user['players']]

    context = {
        'user_list': user_list,
        'league_name': league_name
    }

    for user in user_list:
        print(user['display_name'])

    return render(request, 'homepage/index.html', context)
