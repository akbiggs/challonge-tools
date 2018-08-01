#!/usr/bin/env python3


"""Seeds a Challonge tournament based on gaR PR rankings.

Usage:

    python garpr_seeds_challonge.py <tourney_name>

Replace <tournament_name> with the name of the tournament in the URL.
For example, for www.challonge.com/mtvmlee72:

   python garpr_seeds_challonge.py mtvmelee72
"""


import argparse
import challonge
import sys

import defaults
import garpr_seeds
import shuffle_seeds
import util
import util_challonge


# TODO: These sys.stderr calls may need to be changed to logging calls

def _sort_by_seeds(values, seeds):
    """Sorts a list of values by corresponding seed values.

  e.g. ["x", "y", "z"], [2, 1, 3] => ["y", "x", "z"]

  Args:
    values: A list of values.
    seeds: A list of the same size as |values| containing Challonge seeds
           for those values.

  Returns:
    The list of values, but resorted using the order of the seeds.
  """
    enumerated_values = list(enumerate(values))
    sorted_enumerated_values = sorted(enumerated_values, key=lambda x: seeds[x[0]])
    return [x[1] for x in sorted_enumerated_values]


def seed_tournament(tourney_name, region='', shuffle=False):
    """Return a list of participants sorted by seed, ascending."""
    # Make sure the tournament exists.
    tourney_name = util_challonge.parse_tourney_name(tourney_name)
    tourney_url = "http://challonge.com/{0}".format(tourney_name)
    if not util_challonge.get_tourney_info(tourney_name):
        sys.stderr.write("No tourney exists at {0}.\n".format(tourney_url))
        sys.exit(1)

    # Get the seeds for the participants.
    participants = challonge.participants.index(tourney_name)
    participant_names = [util_challonge.get_participant_name(x) for x in participants]
    ranks = garpr_seeds.get_garpr_ranks(participant_names, region)
    new_seeds = garpr_seeds.ranks_to_seeds(ranks)

    # Let the user know which participants couldn't be found.
    for i, participant in enumerate(participants):
        if ranks[i] == garpr_seeds.UNKNOWN_RANK:
            print(
                "Could not find gaR PR info for {0}, seeding {1}\n".format(
                    participant_names[i], new_seeds[i]
                ),
                end=" ",
            )

    # Sort the participants on Challonge. They need to be sorted
    # before updating their seed, or else the order of the seeds could get
    # disrupted from reordering as seeds are changed.
    sorted_participants = _sort_by_seeds(participants, new_seeds)

    # Shuffle the seeds to vary up the bracket a bit.
    if shuffle:
        shuffled_seeds = shuffle_seeds.get_shuffled_seeds(len(participants))
        sorted_participants = _sort_by_seeds(sorted_participants, shuffled_seeds)

    return sorted_participants


def update_seeds(tourney_name, sorted_participants):
    """This is a helper function to be called from the webapp."""
    for i, participant in enumerate(sorted_participants, 1):
        challonge.participants.update(tourney_name, participant["id"], seed=i)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Seeds a tournament on Challonge from gaR PR rankings.",
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
    argparser.add_argument(
        "--region",
        default=defaults.DEFAULT_REGION,
        help="the region from which the gaR PR rankings "
        "should be pulled from. For example, in the "
        "URL http://garpr.com/googlemtv/players, the "
        "region is 'googlemtv'",
    )
    argparser.add_argument(
        "--shuffle",
        action="store_true",
        help="shuffles the seeds after seeding with gaR PR",
    )
    argparser.add_argument(
        "--print_only",
        action="store_true",
        help="just prints the seeds without changing the tournament",
    )
    args = argparser.parse_args()

    # Read config info.
    initialized = util_challonge.set_challonge_credentials_from_config(args.config_file)
    if not initialized:
        sys.exit(1)

    sorted_participants = seed_tournament(args.tourney_name,
                                          args.region,
                                          args.shuffle)

    for i, participant in enumerate(sorted_participants, 1):
        print(
            "{0}. {1}".format(i, util_challonge.get_participant_name(participant))
        )
        if not args.print_only:
            challonge.participants.update(tourney_name, participant["id"], seed=i)

    if not args.print_only:
        print("Tournament updated; see seeds at {0}/participants.".format(tourney_url))
