#!/usr/bin/env python3


"""Utilities for shuffling seeds in a tournament.

These functions help you shuffle a bracket while still preserving the projected
placement of each participant at the end of the tournament. This helps
randomize tournaments while still keeping things balanced.

Examples:

1. python shuffle_seeds.py 9
     => [1, 2, 3, 4, 6, 5, 8, 7, 9]

Returns the newly shuffled seeding order for a tournament with a given number
of participants. Each number indicates where the corresponding seed should be
listed.

2. python shuffle_seeds.py "Neal, Bryan, Paragon, gaR, Admiral Lightning Bolt, Eden"
     => ['Neal', 'Bryan', 'Paragon', 'gaR', 'Eden', 'Admiral Lightning Bolt']

Returns the newly shuffled order of participants from a list of participant names.
Participants should be ordered from 1st seed to last seed. Leading and trailing
spaces in the participant names are stripped.
"""

import argparse
import numbers
import random
import sys

import util


def _get_num_participants_in_first_round(num_participants):
    """Gets the number of people in the first round of a tourney.

    Args:
      num_participants: The number of total participants in the tourney.

    Returns:
      The number of people who will be playing in the tournament's first
      round.
    """
    if num_participants <= 0:
        raise ValueError("Invalid number of participants for a tourney.")
    if num_participants <= 2:
        return num_participants

    # If the bracket size is a power of two, everybody gets to play in
    # the first round.
    nearest_smaller_power_of_two = 2 ** (num_participants.bit_length() - 1)
    if nearest_smaller_power_of_two == num_participants:
        return num_participants

    # Otherwise, we have an awkwardly-sized bracket.
    # For each leftover participant, we match them up with a low seed from a
    # nice power-of-two-sized bracket, with everyone else getting a bye.
    num_leftover_participants = num_participants - nearest_smaller_power_of_two
    return num_leftover_participants * 2


# TODO: We use this method for non-shuffling related things. Either rename
# this module or move this method into a separate module.
def get_num_participants_placing_last(num_participants, double_elimination=True):
    """Gets the number of people who place last in a tourney of
    num_participants.

    Args:
      num_participants: The number of participants in the tourney.
      double_elimination: Whether the tournament is double-elimination.

    Returns:
      The number of people who will place last in that tourney.

    Raises:
      ValueError: if num_participants <= 0.
    """
    if num_participants == 1:
        return 1

    # <= 4 is a bit of a weird case, so we handle it specially.
    # TODO: reason through what's making the bucket size zero for the value 4,
    # too tired ATM
    if num_participants <= 4:
        return 1 if double_elimination else 2

    num_in_first_round = _get_num_participants_in_first_round(num_participants)
    num_losing_in_first_round = num_in_first_round // 2
    if not double_elimination:
        return num_losing_in_first_round

    # We just knocked a bunch of people into loser's. The second winner's round
    # is always power-of-two-sized, where half the people will get knocked into
    # round two of losers. These two groups of people are combined to form the
    # initial loser's bracket. Half the people who fall into the first round of
    # the loser's bracket will place last.
    num_in_second_winners_round = num_participants - num_losing_in_first_round
    num_losing_in_second_winners_round = num_in_second_winners_round // 2
    num_in_first_losers_round = _get_num_participants_in_first_round(
        num_losing_in_first_round + num_losing_in_second_winners_round
    )
    num_losing_in_first_losers_round = num_in_first_losers_round // 2
    return num_losing_in_first_losers_round


def _get_bucket_sizes(num_participants):
    """Get the size of buckets in which seeds can be randomized.

    A bucket is a group of people where the seedings can be randomized
    "safely", i.e. without messing with their projected final placement
    in the loser's bracket.

    Args:
      num_participants: The number of participants in the tournament.

    Yields:
      A list of numbers, one for each bucket. Each number corresponds
      to the number of people in the corresponding bucket. Each bucket
      has at least one person in it. The buckets are yielded from last
      place to first place.
    """
    # All the people who are projected to come in last can be rearranged freely
    # amongst each other without messing with their projected final placement
    # in a double-elimination bracket, so they fall into their own bucket.
    # Once those people are eliminated, the next bucket can be determined
    # by solving for a tournament without the eliminated people. This approach
    # can be applied repeatedly to figure out all the buckets.
    while num_participants > 0:
        bucket_size = get_num_participants_placing_last(num_participants)
        yield bucket_size

        num_participants = num_participants - bucket_size


def _get_buckets(num_participants):
    """Gets a list of buckets of seeds for a tourney with num_participants.

    Args:
      num_participants: The number of participants in the tourney.

    Yields:
      A list for each bucket. Each bucket is a list of numbers
      corresponding to the seeds who fall into that bucket. Buckets are yielded
      from last place (largest bucket) to first place (smallest bucket).
    """
    last_seed_in_bucket = num_participants
    for bucket_size in _get_bucket_sizes(num_participants):
        top_seed_in_bucket = last_seed_in_bucket - bucket_size + 1
        yield list(range(top_seed_in_bucket, last_seed_in_bucket + 1))

        last_seed_in_bucket = top_seed_in_bucket - 1


def get_shuffled_seeds(num_participants):
    """Get randomized seedings for a tournament with num_participants.

    This is not fully randomized, but instead uses a bucket approach,
    where the final projected placements of the participants are unaffected.
    This is nice for varying who gets matched up in a tourney while still
    preserving the overall benefits of seeding.

    Args:
      num_participants: The number of participants in the tournament.

    Returns:
      A list of seeds to use for the tournament. For a given seed X, the value
      at index X - 1 is their randomized seed to use for the tournament.
    """
    shuffled_buckets = [util.shuffle(x) for x in _get_buckets(num_participants)]

    # Buckets are ordered from last place to first place, so we need to reverse
    # them to get the seeds ordered from first to last.
    return util.flatten(reversed(shuffled_buckets))


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="shuffles seeds while preserving project placement",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    argparser.add_argument(
        "participants",
        help="either a number of participants or " "comma-separated participant names",
    )
    argparser.add_argument(
        "--seed", type=int, default=None, help="seed for random number generation"
    )
    args = argparser.parse_args()

    if args.seed:
        random.seed(args.seed)

    if args.participants.isdigit():
        num_participants = int(args.participants)
        print(get_shuffled_seeds(num_participants))
    else:
        participants = [x.strip() for x in args.participants.split(",")]
        shuffled_seeds = get_shuffled_seeds(len(participants))

        # participants[0] is the first seed, so we subtract 1 from the seed number
        # to get the index of the participant.
        shuffled_participants = [participants[seed - 1] for seed in shuffled_seeds]
        print(shuffled_participants)
