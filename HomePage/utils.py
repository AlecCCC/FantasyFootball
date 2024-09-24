import os
from datetime import datetime, timedelta

import requests
import json


# Fetch league info
def get_league_info(league_id):
    league_info_url = f'https://api.sleeper.app/v1/league/{league_id}'
    response = requests.get(league_info_url).json()
    return {
        'league_name': response['name'],
        'league_avatar': response['avatar']
    }


# Fetch rosters in a league
def get_rosters_in_league(league_id):
    rosters_url = f'https://api.sleeper.app/v1/league/{league_id}/rosters'
    response = requests.get(rosters_url).json()
    roster_ids = [{'roster_id': roster['roster_id'], 'owner_id': roster['owner_id'],
                   'wins': roster['settings'].get('wins', 0),
                   'ties': roster['settings'].get('ties', 0),
                   'losses': roster['settings'].get('losses', 0)} for roster in response]
    return roster_ids


# Fetch users in a league
def get_users_in_league(league_id):
    users_url = f'https://api.sleeper.app/v1/league/{league_id}/users'
    response = requests.get(users_url).json()
    user_list = []
    for user in response:
        team_name = user['metadata'].get('team_name', '')
        if not team_name:
            team_name = user['display_name']

        user_list.append({
            'user_id': user['user_id'],
            'team_name': team_name,
            'display_name': user['display_name'],
            'avatar': user['avatar']
        })
    return user_list

def get_weekly_matchups(league_id, week):
    weekly_matchups_url = f'https://api.sleeper.app/v1/league/{league_id}/matchups/{week}'
    weekly_matchups = requests.get(weekly_matchups_url).json()
    return weekly_matchups
def get_nfl_state():
    nfl_data ='https://api.sleeper.app/v1/state/nfl'
    nfl_data = requests.get(nfl_data).json()
    return nfl_data

# Populate players and starters for each user
def populate_players_and_starters(league_id, user_list, roster_map):
    rosters_url = f'https://api.sleeper.app/v1/league/{league_id}/rosters'
    response = requests.get(rosters_url).json()

    for roster in response:
        owner_id = roster['owner_id']
        for user_data in user_list:
            if user_data['user_id'] == owner_id:
                user_data['players'] = roster.get('players', [])
                user_data['starters'] = roster.get('starters', [])
                break
    return user_list


# Convert player IDs to player names
def convert_player_ids_to_names(user_list):
    with open('nfl_players_cache.json', 'r') as file:
        player_data = json.load(file)

    for user_data in user_list:
        # Ensure 'players' is initialized before processing
        user_data['players'] = user_data.get('players', [])

        updated_players = []
        for player_id in user_data['players']:
            if player_id == '0':
                updated_players.append({
                    'full_name': 'Injured Player',
                    'position': 'Injured',
                    'player_id': '0'
                })
            else:
                player_info = player_data.get(player_id, {})
                updated_players.append({
                    'full_name': player_info.get('full_name', player_id),
                    'position': player_info.get('position', 'Unknown Position'),
                    'player_id': player_info.get('player_id', 'Unknown Player ID')
                })
        user_data['players'] = updated_players

        # Ensure 'starters' is initialized before processing
        user_data['starters'] = user_data.get('starters', [])

        updated_starters = []
        for starter_id in user_data['starters']:
            if starter_id == '0':
                updated_starters.append({
                    'full_name': 'Out Player',
                    'position': 'NA',
                    'player_id': '0'
                })
            else:
                player_info = player_data.get(starter_id, {})
                updated_starters.append({
                    'full_name': player_info.get('full_name', starter_id),
                    'position': player_info.get('position', 'Unknown Position'),
                    'player_id': player_info.get('player_id', 'Unknown Player ID')
                })
        user_data['starters'] = updated_starters

    return user_list


def get_api_data(url, file_name):
    CACHE_DURATION = timedelta(hours=6)  # Cache validity period

    def fetch_data_from_api():
        print("Fetching data from API...")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Save the data to a local cache file
            with open(file_name, 'w') as f:
                json.dump(data, f)
            return data
        else:
            response.raise_for_status()

    def load_data():
        if os.path.exists(file_name):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_name))
            if datetime.now() - file_mod_time < CACHE_DURATION:
                print(f"Loading data from cache file {file_name}...")
                with open(file_name, 'r') as f:
                    return json.load(f)
        # If cache is expired or doesn't exist, fetch new data
        return fetch_data_from_api()

    # Return the loaded or freshly fetched data
    return load_data()


def create_team_matchup_dicts(weekly_matchups):
    from collections import defaultdict

    # Group teams by matchup_id
    teams_by_matchup = defaultdict(list)
    for team in weekly_matchups:
        teams_by_matchup[team['matchup_id']].append(team)

    result = []

    # Process each matchup
    for matchup_id, teams in teams_by_matchup.items():
        if len(teams) == 2:  # Ensure we only process matchups with exactly two teams
            team_dicts = []
            for team in teams:
                # Create the team info with the new fields included
                team_info = {
                    'team_name': team['team_name'],  # Team name
                    'avatar': team.get('avatar', None),  # Avatar URL
                    'wins': team.get('wins', 0),  # Wins
                    'ties': team.get('ties', 0),  # Ties
                    'losses': team.get('losses', 0),  # Losses
                    'points': team['points'],  # Total points
                    'players': [],  # Initialize players list
                    'positions': [],  # Initialize positions list
                    'player_id': [],  # Initialize player IDs list
                }

                # Process each starter in the team's 'starters' list
                for starter_id in team['starters']:
                    # Find the corresponding player in the 'players' list by matching player_id
                    starter = next((player for player in team['players'] if player['player_id'] == starter_id), None)

                    # If starter found, append their details to the team_info
                    if starter:
                        player_info = {
                            'full_name': starter['full_name'],
                            'position': starter['position'],
                            'player_id': starter['player_id'],
                            'points': starter['points']
                        }
                        # Append player info to respective lists
                        team_info['players'].append(player_info)
                        team_info['positions'].append(starter['position'])
                        team_info['player_id'].append(starter['player_id'])

                # Append the team's info to team_dicts
                team_dicts.append(team_info)

            # Append the final matchup info with both teams
            result.append({
                'matchup_id': matchup_id,
                'teams': team_dicts
            })

    # Return the result containing the processed matchups
    return result
