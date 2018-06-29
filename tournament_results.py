#!/usr/bin/env python3
"""
Get the results a Challonge tournament and use the information to update
the Smash results spreadsheet.

Pre-Reqs:
1. Set up OAuth: https://developers.google.com/drive/api/v3/quickstart/python
2. Download the "My Project*.json" authentication file (this is the value for
   the --oauth parameter)
3. Share the results spreadsheet with with "Edit" rights to the "client_email"
   listed in the OAuth file. Should be "@*.iam.gserviceaccount.com".
4. Reflect briefly on how much more work this was than typing in the results
   by hand.
5. Run the script

"""
import argparse
import challonge
import configparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import re
from requests.exceptions import HTTPError
import sys

import defaults
import util_challonge

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
                    description="Parse the results of a Challonge tournament, "
                                "and post the results to a Google Sheet. "
                                "Make sure to do the work in the header of "
                                "this file before running it.",
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter
                )
    argparser.add_argument(
        "tourney_num_file",
        default='TOURNEY_NUM',
        help="file containing what tournament we're on",
    )
    argparser.add_argument(
        "--config_file",
        default=defaults.DEFAULT_CONFIG_FILENAME,
        help="the config file to read your Challonge credentials from",
    )
    argparser.add_argument(
        "--oauth",
        default="client_secret.json",
        help="OAuth JSON file to access the Drive API"
    )

    args = argparser.parse_args()

    # We need to initialize our Challonge credentials before we can
    # make any API calls.
    initialized = util_challonge.\
        set_challonge_credentials_from_config(args.config_file)
    if not initialized:
        sys.exit(1)

    if not os.path.isfile(args.oauth):
        print("JSON authentication file '{}' not found to access Sheets.\n"
              "Make sure you followed the OAuth steps in the header to\n"
              "download the client secret file.".format(args.oauth))
        sys.exit(1)

    config_parser = configparser.RawConfigParser()
    config_parser.read(args.config_file)

    try:
        SPREADSHEET_KEY = config_parser.get('Sheets', 'spreadsheet_key')
    except configparse.Error as err:
        sys.stderr.write("Be sure to set 'spreadsheet_key' in config file: {}"
                         .format(err))
        sys.exit(1)

    # Read previous tournament number
    with open(args.tourney_num_file) as f:
        TOURNEY_NUM = int(f.read()) + 1

    tourney_name = "mtvmelee{}".format(TOURNEY_NUM)

    try:
        tourney_info = challonge.tournaments.show(tourney_name)
    except HTTPError:
        sys.stderr.write("Couldn't find tournament: {}\n".format(tourney_name))
        sys.exit(1)

    players = challonge.participants.index(tourney_name)

    top_3 = [0] * 3
    num_top_3 = 0
    for player in players:
        rank = player['final_rank']
        if rank in {1, 2, 3}:
            top_3[rank-1] = util_challonge.get_participant_name(player)
            num_top_3 += 1

            if num_top_3 == 3:
                break

    # Throw an exception if there aren't 3 players in the top 3
    if num_top_3 != 3:
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
        from_json_keyfile_name(args.oauth, scope)

    gc = gspread.authorize(credentials)

    wks = gc.open_by_key(SPREADSHEET_KEY).sheet1
    wks.insert_row(results, index=2, value_input_option='USER_ENTERED')

    with open(args.tourney_num_file, "w") as f:
        f.write(str(TOURNEY_NUM))
