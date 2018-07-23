#!/usr/bin/env python3


import argparse
import challonge
import itertools
import re
import requests

import defaults


UNKNOWN_RANK = -1


"""Generates seeds for a tournament from gaR PR. http://www.garpr.com

Unknown people will be made into last-place seeds, in order of appearance.

Requires internet access to access gaR PR.

Usage:

  python garpr_seeds "Bryan, gaR, Admiral, Admiral Lightning Bolt, NotOnGaRPR"
      => [3, 1, 2, 5, 4, 6]
"""


def _fetch_garpr_rankings(region):
    """Fetches the gaR PR rankings from a given region.

    Args:
      region: The region of the gaR PR tournament.

    Returns:
      A list of ranking responses for that region. Basically the same response
      that you would get from querying /rankings using the gaR PR API.
    """
    rankings_url = "https://www.garpr.com:3001/{0}/rankings".format(region)
    return requests.get(rankings_url).json()["ranking"]


def _find_ranking_for_name(name, rankings):
    """Finds a user's ranking info.

    Args:
      name: The name of the user whose ranking we want to find.
      rankings: The list of gaR PR ranking objects we wanna look through.

    Returns:
      The ranking object that corresponds to that user, or None if no
      ranking already exists.
    """
    name = name.lower()

    # GarPR handles multiple tags with either "Tag / OtherTag" or
    # "Tag (OtherTag).
    if "/" in name:
        names = {name.split(" / ")}
    elif "(" in name:
        m = re.search("(.*)\s+\((.*)\)", name)
        names = {m.group(1), m.group(2)}
    else:
        names = {name}

    for ranking in rankings:
        if ranking["name"].lower() in names:
            return ranking
    return None


def _get_rank(ranking):
    """Retrieves a rank from a gaR PR ranking.

    Args:
      ranking: The gaR PR ranking response object.

    Returns:
      The player's rank, or UNKNOWN_RANK if their ranking is unknown.
    """
    return ranking["rank"] if ranking else UNKNOWN_RANK


def ranks_to_seeds(ranks):
    """Squashes ranks so they're ordered from 1 to N and can be used as seeds.

    e.g. [4, 6, UNKNOWN_RANK, 2, UNKNOWN_RANK] => [2, 3, 4, 1, 5]

    Args:
      ranks: The numerical ranks of the players from gaR PR. UNKNOWN_RANK should
             be used if the player has no ranks. All ranks are expected to be
             unique.

    Returns:
      The seeds, in the same order as the original ranks. The order of values is
      sequential, such that the largest difference between any two ranks in a
      sorted list of ranks is 1, and all unknown ranks are converted to
      last-place seeds in order of appearance.
    """
    # Our approach is to sort the ranks since seeds should just be the
    # sorted order of the known ranks. We filter out unknown ranks since they'd
    # disrupt the order.
    sorted_known_ranks = [x for x in sorted(ranks) if x != UNKNOWN_RANK]

    next_last_place_seed = len(sorted_known_ranks) + 1
    seeds = []
    for i, rank in enumerate(ranks):
        if rank == UNKNOWN_RANK:
            seeds.append(next_last_place_seed)
            next_last_place_seed = next_last_place_seed + 1
        else:
            seeds.append(sorted_known_ranks.index(rank) + 1)

    return seeds


def get_garpr_ranks(names, region):
    """Gets the seeds for names based off of gaR PR rankings.

    Args:
      names: A list of names of the people you want to get ranks for. These
             names should correspond to their name on the gaR PR.
      region: The gaR PR region that you want to pull rankings from.

    Returns:
      A list of ranks for those players. UNKNOWN_RANK will be returned as the
      rank for any player that is not currently on the gaR PR.
    """
    rankings = _fetch_garpr_rankings(region)
    name_rankings = [_find_ranking_for_name(name, rankings) for name in names]
    ranks = [_get_rank(ranking) for ranking in name_rankings]
    return ranks


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Generates seeds for a tournament from gaR PR rankings.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argparser.add_argument("names", help="the names of the players to seed")
    argparser.add_argument(
        "--region",
        default=defaults.DEFAULT_REGION,
        help="the region from which the gaR PR rankings "
        "should be pulled from. For example, in the "
        "URL http://garpr.com/googlemtv/players, the "
        "region is 'googlemtv'",
    )
    args = argparser.parse_args()

    region = args.region
    names = [x.strip() for x in args.names.split(",")]
    ranks = get_garpr_ranks(names, region)
    print(ranks_to_seeds(ranks))
