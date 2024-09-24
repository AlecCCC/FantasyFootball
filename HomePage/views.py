import pprint

import requests
from datetime import datetime, timedelta
from django.shortcuts import render
from .utils import (
    get_league_info,
    get_rosters_in_league,
    get_users_in_league,
    populate_players_and_starters,
    convert_player_ids_to_names, get_api_data, get_nfl_state, get_weekly_matchups, create_team_matchup_dicts
)


def index(request, league_id):
    nfl_data = get_api_data('https://api.sleeper.app/v1/players/nfl/', 'nfl_players_cache.json')
    print(f"Total players loaded: {len(nfl_data)}")
    league_info = get_league_info(league_id)
    league_name = league_info['league_name']
    league_avatar = league_info['league_avatar']
    roster_ids = get_rosters_in_league(league_id)
    print(roster_ids)
    user_list = get_users_in_league(league_id)
    roster_map = {item['owner_id']: item['roster_id'] for item in roster_ids}
    user_list = populate_players_and_starters(league_id, user_list, roster_map)
    user_list = convert_player_ids_to_names(user_list)
    user_list = [user for user in user_list if user['players']]
    context = {
        'user_list': user_list,
        'league_name': league_name,
        'league_avatar': league_avatar,
        'league_id': league_id  # Pass league_id to the template
    }
    return render(request, 'HomePage/index.html', context)


import json
with open('nfl_players_cache.json', 'r') as f:
    player_info = json.load(f)


def matchups(request, league_id):
    data = get_nfl_state()
    week = data.get('week')
    rosters = get_rosters_in_league(league_id)
    user_list = get_users_in_league(league_id)
    weekly_matchups = get_weekly_matchups(league_id, 3)

    # Add player details to matchups
    for matchup in weekly_matchups:
        for i, player_id in enumerate(matchup['players']):
            if player_id in player_info:
                player = player_info[player_id]
                position = player.get('position', 'Unknown')
                full_name = player.get('full_name', 'Unknown')

                matchup['players'][i] = {
                    'player_id': player_id,
                    'full_name': full_name,
                    'position': position,
                    'points': matchup['players_points'].get(player_id, 0.0)  # Include player points if available
                }
    #
    for roster in rosters:
        matching_user = next((user for user in user_list if user['user_id'] == roster['owner_id']), None)
        # If a match is found, update the roster with team_name and avatar
        if matching_user:
            roster['team_name'] = matching_user['team_name']
            roster['avatar'] = matching_user['avatar']

    # Grab a rosters, wins, ties, losses, team_name, and avatar_id to put in weekly matchups.
    for matchup in weekly_matchups:
        matching_roster = next((roster for roster in rosters if roster['roster_id'] == matchup['roster_id']), None)
        if matching_roster:
            matchup['wins'] = matching_roster['wins']
            matchup['ties'] = matching_roster['ties']
            matchup['losses'] = matching_roster['losses']
            matchup['team_name'] = matching_roster['team_name']
            matchup['avatar'] = matching_roster['avatar']

    weekly_matchups = create_team_matchup_dicts(weekly_matchups)
    context = {
        'league_id': league_id,
        'rosters':rosters,
        'weekly_matchups': weekly_matchups,
        'user_list': user_list
    }

    return render(request, "Matches/matchups.html", context)
