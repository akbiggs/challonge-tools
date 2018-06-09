#!/usr/bin/env python3


"""Various utility functions that aren't related to Challonge things."""


import argparse
import random


def shuffle(values):
    """Returns the list of values shuffled.

    This is different from random.shuffle because it returns a new list
    instead of operating in-place.

    Args:
      values: A list of arbitrary values.

    Returns:
      The values shuffled into a random order.
    """
    return random.sample(values, len(values))


def flatten(lists):
    """Flattens a list of lists into a single list of values.

    Args:
      lists: A list of lists.

    Returns:
      The list flattened into a single list, with the same order of values.
    """
    return [x for sublist in lists for x in sublist]


def str_to_bool(s):
    """Converts a string value to a boolean value.

    Args:
      s: The string to convert to a boolean value.

    Raises:
      argparse.ArgumentTypeError: If the string doesn't correspond to a bool.

    Returns:
      The corresponding boolean value for the string.
    """
    if s.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif s.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def prompt_yes_no(prompt):
    """Prompts the user to respond yes/no to a question.

    Asks repeatedly until valid input is given.

    Args:
      prompt: The prompt to use. This should not include "[y/n]".

    Returns:
      True if the user answered yes, False if they answered yes.
    """
    while True:
        print((prompt + " [y/n]"), end=" ")

        choice = input().lower()
        try:
            return str_to_bool(choice)
        except argparse.ArgumentTypeError:
            print("Invalid response. Please say 'y' or 'n'.")
