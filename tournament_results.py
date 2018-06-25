#!/usr/bin/env python3
"""
Get the results a Challonge tournament and use the information to update
the Smash results spreadsheet.

Pre-Reqs:
1. Set up OAuth: https://developers.google.com/drive/api/v3/quickstart/python
2. 

"""
import argparse
import challonge
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import sys

import defaults
import util_challonge

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
                    description="Parse the results of a Challonge tournament.",
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter
                )
    argparser.add_argument(
        "tourney_name",
        help="the name of the tourney to create an amateur bracket for",
    )
    argparser.add_argument(
        "--config_file",
        default=defaults.DEFAULT_CONFIG_FILENAME,
        help="the config file to read your Challonge credentials from",
    )
    argparser.add_argument(
        "--auth_json",
        help="json file to access Drive API"
    )

    args = argparser.parse_args()

    # We need to initialize our Challonge credentials before we can
    # make any API calls.
    initialized = util_challonge.\
        set_challonge_credentials_from_config(args.config_file)
    if not initialized:
        sys.exit(1)

    tourney_name = util_challonge.parse_tourney_name(args.tourney_name)
    tourney_info = challonge.tournaments.show(tourney_name)
    players = challonge.participants.index(tourney_name)

    top_3 = [0] * 3
    for player in players:
        rank = player['final_rank']
        if rank in {1, 2, 3}:
            top_3[rank-1] = util_challonge.get_participant_name(player)

    # Throw an exception if there aren't 3 players in the top 3
    if any(not p for p in top_3):
        raise Exception("Top 3 could not be found. Is the tournament over?")

    date = tourney_info['started_at'].strftime('%b %e, %Y')
    match = re.search(r'\d+$', tourney_name)
    weekly = match.group(0)

    results = []
    results.append(weekly)
    results.append(date)

    for pl in top_3:
        results.append(pl)

    bracket_url = "https://challonge.com/{}".format(tourney_name)
    results.append(bracket_url)

    print('Results:', results)

    # Add the results to the results spreadsheet

    # Auth to access the spreadsheet
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = ServiceAccountCredentials.\
        from_json_keyfile_name('client_secret.json', scope)

    gc = gspread.authorize(credentials)

    # TODO(timkovich): Move this key to the .ini file
    SPREADSHEET_KEY = "1-foClIqQ-i8rUkdhl2jSYHUP_lj65EBNmrzaZ4R48eU"
    wks = gc.open_by_key(SPREADSHEET_KEY).sheet1
    wks.insert_row(results, index=2, value_input_option='USER_ENTERED')
