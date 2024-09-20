# HomePage/views.py
from django.shortcuts import render
import requests
import json
import os
from datetime import datetime, timedelta
from django.shortcuts import render
from django.core.signing import Signer, BadSignature

from django.shortcuts import render
from .utils import (
    get_league_info,
    get_rosters_in_league,
    get_users_in_league,
    populate_players_and_starters,
    convert_player_ids_to_names, get_api_data
)


def index(request):
    nfl_data = get_api_data('https://api.sleeper.app/v1/players/nfl/', 'nfl_players_cache.json')
    print(f"Total players loaded: {len(nfl_data)}")

    # Get league_id from the GET request, defaulting to a specific ID if not provided
    league_id = request.GET.get('league_id', '1119837649793110016')

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
        'league_avatar': league_avatar
    }

    # Render the template with the context
    return render(request, 'HomePage/index.html', context)


def matchups(request):


    return render(request, "Matches/matchups.html")
