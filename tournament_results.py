#!/usr/bin/env python3
import argparse
import challonge
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

    # Make sure we did get the top 3 players
    if any(not p for p in top_3):
        raise Exception("Top 3 could not be found. Is the tournament over?")

    date = tourney_info['started_at'].strftime('%b %e, %Y')
    match = re.search(r'\d+$', tourney_name)
    weekly = match.group(0)

    print("Weekly #:", weekly)
    print("Date:", date)
    for pl, num in zip(top_3, ["1st", "2nd", "3rd"]):
        print("{}: {}".format(num, pl))
    print("Bracket: https://challonge.com/{}".format(tourney_name))

    # TODO(timkovich): Using sheets API
    # https://developers.google.com/sheets/api/quickstart/python
    # 0. Auth
    # 1. Insert new row
    # 2. Insert the above values into that row
