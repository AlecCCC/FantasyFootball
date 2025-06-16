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
    data = get_nfl_state()
    current_week = data.get('week')
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
        'league_id': league_id,
        'current_week': current_week
    }
    return render(request, 'HomePage/index.html', context)


import json
with open('nfl_players_cache.json', 'r') as f:
    player_info = json.load(f)


def matchups(request, league_id, current_week):
    league_info = get_league_info(league_id)
    league_name = league_info['league_name']
    league_avatar = league_info['league_avatar']
    data = get_nfl_state()
    fetched_week = data.get('week')  # Use a different variable name to store the fetched week
    rosters = get_rosters_in_league(league_id)
    user_list = get_users_in_league(league_id)
    weekly_matchups = get_weekly_matchups(league_id, current_week)
    print(f"Current week: {fetched_week}")

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
                    'points': matchup['players_points'].get(player_id, 0.0)
                }
    previous_week = max(1, current_week - 1)  # Ensure week doesn't go below 1
    next_week = current_week + 1  # Assuming no upper limit for weeks


    # Populate rosters with user info
    for roster in rosters:
        matching_user = next((user for user in user_list if user['user_id'] == roster['owner_id']), None)
        if matching_user:
            roster['team_name'] = matching_user['team_name']
            roster['avatar'] = matching_user['avatar']

    # Add wins, ties, losses to matchups
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
        'league_name':league_name,
        'league_avatar':league_avatar,
        'league_id': league_id,
        'rosters': rosters,
        'weekly_matchups': weekly_matchups,
        'user_list': user_list,
        'fetched_week': fetched_week,
        'current_week': current_week,
        'previous_week': previous_week,
        'next_week': next_week,
    }

    return render(request, "Matches/matchups.html", context)


def standings(request, league_id):
    league_info = get_league_info(league_id)
    rosters = get_rosters_in_league(league_id)
    user_list = get_users_in_league(league_id)
    league_name = league_info['league_name']
    league_avatar = league_info['league_avatar']

    roster_dict = {roster['owner_id']: roster for roster in rosters}

    for user in user_list:
        owner_id = user['user_id']
        if owner_id in roster_dict:
            user['wins'] = roster_dict[owner_id]['wins']
            user['losses'] = roster_dict[owner_id]['losses']
            user['ties'] = roster_dict[owner_id]['ties']

    # Ensure only users with wins, losses, and ties are included
    user_list = [user for user in user_list if 'wins' in user and 'losses' in user and 'ties' in user]

    # Sort user_list by wins in descending order
    user_list = sorted(user_list, key=lambda user: user['wins'], reverse=True)

    data = get_nfl_state()
    current_week = data.get('week')



    context = {
        'league_name': league_name,
        'league_avatar': league_avatar,
        'user_list': user_list,
        'rosters': rosters,
        'league_id': league_id,
        'current_week': current_week,
    }
    return render(request, 'standings.html', context)

# League ID changes to new season, so I need to use a previous league ID.
