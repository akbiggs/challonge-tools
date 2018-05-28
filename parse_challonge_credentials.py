#!/usr/bin/env python

"""TODO
"""


import challonge
import ConfigParser
import sys


# Name of the default config file.
_DEFAULT_CONFIG_FILENAME = "credentials.ini"


# Section in the config file with challonge credential info.
_CHALLONGE_CONFIG_CREDENTIAL_SECTION = "Challonge Credentials"
_CHALLONGE_CONFIG_USER_OPTION = "user"
_CHALLONGE_CONFIG_API_KEY_OPTION = "api_key"


def _parse_challonge_credentials_from_config_file(config_filename):
  """Parses Challonge credentials from a config file.
  
  Args:
    config_filename: The filename of the config file to parse.
 
  Raises:
    ConfigParser.NoSectionError:
      If the file doesn't exist or the Challonge Credentials section doesn't
      exist in the config file.

    ConfigParser.NoOptionError:
      If the user or api_key options don't exist in the config file.
 
  Returns:
    A dictionary with {"user", "api_key"} keys parsed from the config file.
  """
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(config_filename)

  user = config_parser.get(
      _CHALLONGE_CONFIG_CREDENTIAL_SECTION,
      _CHALLONGE_CONFIG_USER_OPTION)
  api_key = config_parser.get(
      _CHALLONGE_CONFIG_CREDENTIAL_SECTION,
      _CHALLONGE_CONFIG_API_KEY_OPTION)
  
  return {"user": user, "api_key": api_key}


if __name__ == "__main__":
  if len(sys.argv) > 2:
    sys.stderr.write("Usage: {0} [<credentials_file>]\n".format(sys.argv[0]))
    sys.exit(1)
  
  if len(sys.argv) == 2:
    config_filename = sys.argv[1]
  else:
    config_filename = _DEFAULT_CONFIG_FILENAME
  
  try:
    credentials = _parse_challonge_credentials_from_config_file(
        config_filename)
  except ConfigParser.Error as err:
    sys.stderr.write("Failed to read credentials from {0}: {1}.\n".format(
        config_filename, err))
    sys.stderr.write(
        "Check {0} for instructions on how to setup your config.".format(
        _DEFAULT_CONFIG_FILENAME))
    sys.exit(1)

  print credentials

