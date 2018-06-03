#!/usr/bin/env python


"""Various common utility functions that interact with Challonge."""


import challonge
import urllib2

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

  challonge.set_credentials(credentials["user"],
                            credentials["api_key"])
  return True


def parse_tourney_name(name_or_url):
  """Parses the URL name of the tournament from its name or URL.

  Useful for sanitizing input.

  Args:
    name_or_url: Either the name at the end of a Challonge URL, or a full
                 Challonge URL.

  Returns:
    Just the name bit at the end of a URL.
  """
  return name_or_url.split("http://challonge.com/")[-1]


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
  except urllib2.HTTPError as err:
    # If we got a 404, we queried fine and no amateur bracket exists,
    # but otherwise we've got an unexpected error, so we escalate it.
    if err.code != 404:
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
  # I got bitten by using "name" instead of "display-name" (there
  # are some weird invitation-based cases where "name" is invalid),
  # so I made this function to help me remember.
  return participant_info["display-name"]

