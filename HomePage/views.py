# HomePage/views.py
from django.shortcuts import render
import requests
import json
import os
from datetime import datetime, timedelta
from django.shortcuts import render
from django.core.signing import Signer, BadSignature
import unicodedata
from django.shortcuts import render
from .utils import (
    get_league_info,
    get_rosters_in_league,
    get_users_in_league,
    populate_players_and_starters,
    convert_player_ids_to_names, get_api_data
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
    year = datetime.now().year
    week = 3

    # Get roster and user data
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
    # Map user_id to player details
    player_mapping = {}
    for user in user_list:
        for player in user['players']:
            player_mapping[player['player_id']] = player  # Map player ID to full player details

    # Make sure roster IDs are mapped correctly
    for user in user_list:
        user['roster_id'] = roster_map.get(user['user_id'])
        user['players'] = user.get('players', [])
        user['starters'] = user.get('starters', [])

    # Fetch weekly matchups data from Sleeper API
    weekly_matchups = requests.get(f'https://api.sleeper.app/v1/league/{league_id}/matchups/{week}').json()

    # Map player IDs in weekly matchups to both player_id and player_name using player_mapping
    def map_player_names(matchup_data, player_map):
        # Map player IDs to both player_id and names for 'players' list
        matchup_data['players'] = [
            {
                'player_id': player_id,
                'full_name': player_map[player_id]['full_name'] if player_id in player_map else player_id
            }
            for player_id in matchup_data['players']
        ]

        # Map player IDs to both player_id and names for 'starters' list
        matchup_data['starters'] = [
            {
                'player_id': player_id,
                'full_name': player_map[player_id]['full_name'] if player_id in player_map else player_id
            }
            for player_id in matchup_data['starters']
        ]

        return matchup_data

    # Apply the mapping for each matchup
    for matchup in weekly_matchups:
        matchup = map_player_names(matchup, player_mapping)

    context = {
        'user_list': user_list,
        'league_id': league_id,
        'weekly_matchups': weekly_matchups
    }

    # Print team name with Unicode support
    print(weekly_matchups)

    return render(request, "Matches/matchups.html", context)
