#!/usr/bin/env python3


"""Shuffles seeds in a Challonge bracket.

Usage:

    python shuffle_seeds_challonge.py <tournament_name>

Replace <tournament_name> with the name of the tournament in the URL.
For example, for www.challonge.com/mtvmlee72:

    python shuffle_seeds_challonge.py mtvmelee72
"""


# Python package imports.
import argparse
import challonge
import sys

# Local imports.
import defaults
import shuffle_seeds
import util
import util_challonge


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="shuffles seeds in a Challonge bracket, preserving "
        "projected placement",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argparser.add_argument(
        "tourney_name",
        help="the name of the Challonge tournament to "
        "shuffle. This is the name at the end of the "
        "URL for your tournament",
    )
    argparser.add_argument(
        "--config_file",
        default=defaults.DEFAULT_CONFIG_FILENAME,
        help="the config file to read your Challonge " "credentials from",
    )
    args = argparser.parse_args()

    initialized = util_challonge.set_challonge_credentials_from_config(args.config_file)
    if not initialized:
        sys.exit(1)

    tourney_name = util_challonge.parse_tourney_name(args.tourney_name)
    tourney_url = "http://challonge.com/{0}".format(tourney_name)
    tourney_info = challonge.tournaments.show(tourney_name)
    if tourney_info["state"] != "pending":
        sys.stderr.write(
            "Can only run {0} on tournaments that haven't "
            "started.\n".format(sys.argv[0])
        )
        sys.exit(1)

    # The participants need to be sorted by seed so their index in the
    # list matches up with the shuffled seeds list.
    participant_infos = sorted(
        challonge.participants.index(tourney_name), key=lambda x: x["seed"]
    )
    num_participants = len(participant_infos)
    new_seeds = shuffle_seeds.get_shuffled_seeds(num_participants)

    for i, new_seed in enumerate(new_seeds):
        participant_info = participant_infos[i]
        if participant_info["seed"] == new_seed:
            continue

        participant_id = participant_info["id"]
        challonge.participants.update(tourney_name, participant_id, seed=new_seed)

    print("Seeds shuffled: {0}/participants".format(tourney_url))
