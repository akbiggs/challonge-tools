#!/usr/bin/env python3


"""Various common utility functions that interact with Challonge."""


import challonge
import re
import requests.exceptions

from parse_challonge_credentials import safe_parse_challonge_credentials_from_config


def set_challonge_credentials_from_config(config_filename):
    """Sets up your Challonge API credentials from info in a config file.

    Args:
      config_filename: The filename of the config file to read your credentials
                       from.
    Returns:
      True if the credentials were set successfully, False otherwise.
    """
    credentials = safe_parse_challonge_credentials_from_config(config_filename)
    if not credentials:
        return False

    challonge.set_credentials(credentials["user"], credentials["api_key"])
    return True


def extract_tourney_name(url):
    """
    Parses the URL name of the tournament from its URL.

    Extracts the subdomain (if applicable) and tourney name from URL.

    @param url: URL of a Challonge tournament.
    @returns: Name of the tournament suitable to use in the Challonge API.
    @raises ValueError: iff the Challonge URL is invalid.

    """
    match = re.match(r'(https?://)?(\w+)?\.?challonge.com/([^/]+)', url)

    if match is None or match.group(3) is None:
        raise ValueError('Invalid Challonge URL: {}.'.format(url))

    _, subdomain, tourney = match.groups()

    if subdomain is None:
        return tourney
    else:
        return '{}-{}'.format(subdomain, tourney)


def tourney_name_to_parts(name):
    """
    Converts a tourney name into a URL.

    name is in the format subdomain-tourney or tourney.

    @returns: (tourney, subdomain).

    """

    parts = name.split('-')
    tourney = parts[-1]

    if len(parts) == 1:
        return tourney, None
    else:
        return tourney, parts[0]


def tourney_name_to_url(name):
    """
    Converts a tourney name into a URL.

    name is in the format subdomain-tourney or tourney.

    @returns: Tourney URL.

    """

    tourney, subdomain = tourney_name_to_parts(name)
    
    if subdomain:
        return 'https://{}.challonge.com/{}'.format(subdomain, tourney)
    else:
        return 'https://challonge.com/{}'.format(tourney)


def get_tourney_info(name):
    """Gets info about the tournament with the given name.

    Args:
      name: The name of the tournament.

    Returns:
      The Challonge response about the tournament info if it exists, None
      if it doesn't.
    """
    # We query for the tourney info using the Challonge API. If we don't get
    # a 404, it exists.
    tourney_info = None
    try:
        tourney_info = challonge.tournaments.show(name)
    except requests.exceptions.HTTPError as err:
        # If we got a 404, we queried fine and no amateur bracket exists,
        # but otherwise we've got an unexpected error, so we escalate it.
        if err.response.status_code != 404:
            raise err

    return tourney_info


def get_participant_name(participant_info):
    """Gets the name to use for a participant on Challonge.

    Args:
      participant_info: A Challonge participant model from the server.

    Returns:
      A string representing the name of the participant, or None if we
      couldn't figure out their name.
    """
    # I got bitten by using "name" instead of "display_name" (there
    # are some weird invitation-based cases where "name" is invalid),
    # so I made this function to help me remember.
    return participant_info["display_name"]
