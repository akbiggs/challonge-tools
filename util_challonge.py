#!/usr/bin/env python


"""Various common utility functions that interact with Challonge."""


import challonge

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
    Just the name bit.
  """
  return name_or_url.split("http://challonge.com/")[-1]

