
import requests
from datetime import datetime, timedelta
from django.shortcuts import render
from .utils import (
    get_league_info,
    get_rosters_in_league,
    get_users_in_league,
    populate_players_and_starters,
    convert_player_ids_to_names, get_api_data, create_team_matchup_dicts
)


def index(request, league_id):
    nfl_data = get_api_data('https://api.sleeper.app/v1/players/nfl/', 'nfl_players_cache.json')
    print(f"Total players loaded: {len(nfl_data)}")

    # Fetch league info using the utility function
    league_info = get_league_info(league_id)
    league_name = league_info['league_name']
    league_avatar = league_info['league_avatar']

    # Get rosters and users in the league
    roster_ids = get_rosters_in_league(league_id)
    user_list = get_users_in_league(league_id)

    # Create a mapping of owner_id to roster_id
    roster_map = {item['owner_id']: item['roster_id'] for item in roster_ids}

    # Populate the players and starters for each user
    user_list = populate_players_and_starters(league_id, user_list, roster_map)

    # Convert player IDs to their respective player names
    user_list = convert_player_ids_to_names(user_list)

    # Remove users with no players
    user_list = [user for user in user_list if user['players']]

    # Context for rendering the template
    context = {
        'user_list': user_list,
        'league_name': league_name,
        'league_avatar': league_avatar,
        'league_id': league_id  # Pass league_id to the template
    }

    # Render the template with the context
    return render(request, 'HomePage/index.html', context)


def matchups(request, league_id):
    league_info = get_league_info(league_id)
    league_name = league_info['league_name']
    league_avatar = league_info['league_avatar']

    year = datetime.now().year
    week = 3

    roster_ids = get_rosters_in_league(league_id)
    user_list = get_users_in_league(league_id)
    roster_map = {item['owner_id']: item['roster_id'] for item in roster_ids}
    user_list = populate_players_and_starters(league_id, user_list, roster_map)
    user_list = convert_player_ids_to_names(user_list)

    # Create player_id to name and position mapping
    player_id_mapping = {}
    for user in user_list:
        user['roster_id'] = roster_map.get(user['user_id'])
        user['players'] = user.get('players', [])  # Ensure 'players' exists
        user['starters'] = user.get('starters', [])  # Ensure 'starters' exists

        for player in user['players']:
            player_id_mapping[player['player_id']] = {
                'full_name': player['full_name'],
                'position': player['position']
            }

    weekly_matchups = requests.get(f'https://api.sleeper.app/v1/league/{league_id}/matchups/{week}').json()

    # Process matchups
    for matchup in weekly_matchups:
        # Find the user with the matching roster_id
        matching_user = next((user for user in user_list if user['roster_id'] == matchup['roster_id']), None)

        if matching_user:
            team_name = matching_user['team_name'] if matching_user['team_name'] != "No Team Name" else matching_user[
                'display_name']
            matchup['team_name'] = team_name
            matchup['avatar'] = matching_user.get('avatar', None)

            matchup['players'] = [
                {
                    'player_id': player_id,
                    'full_name': player_id_mapping.get(player_id, {}).get('full_name', 'Unknown'),
                    'position': player_id_mapping.get(player_id, {}).get('position', 'Unknown'),
                    'points': matchup['players_points'].get(player_id, 0)
                }
                for player_id in matchup['players']
            ]
            matchup['starters'] = [
                {
                    'player_id': player_id,
                    'full_name': player_id_mapping.get(player_id, {}).get('full_name', 'Unknown'),
                    'position': player_id_mapping.get(player_id, {}).get('position', 'Unknown'),
                    'points': matchup['players_points'].get(player_id, 0)
                }
                for player_id in matchup['starters']
            ]
    weekly_matchups = [{key: value for key, value in entry.items() if key != 'players'} for entry in weekly_matchups]

    weekly_matchups = create_team_matchup_dicts(weekly_matchups)

    context = {
        'league_name': league_name,
        'league_avatar': league_avatar,
        'user_list': user_list,
        'league_id': league_id,
        'weekly_matchups': weekly_matchups
    }

    return render(request, "Matches/matchups.html", context)