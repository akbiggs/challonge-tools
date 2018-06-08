#!/usr/bin/env python

"""Tool for parsing Challonge credentials from a config file.

The Challonge API key is something you want to keep secret. I set up this tool
so you can easily parse your Challonge info from a config file that can be
ignored from your git repo instead of hardcoding it into your code.

Example:

  python parse_challonge_config.py my_challonge.ini
    => { user: 'blah', api_key: 'not telling' }

"""


import ConfigParser
import sys

import defaults


# Section in the config file with challonge credential info.
_CHALLONGE_CONFIG_CREDENTIAL_SECTION = "Challonge Credentials"
_CHALLONGE_CONFIG_USER_OPTION = "user"
_CHALLONGE_CONFIG_API_KEY_OPTION = "api_key"


def parse_challonge_credentials_from_config(config_filename):
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

def safe_parse_challonge_credentials_from_config(config_filename):
  """Parses Challonge credentials from a config file with error handling.

  Config parsing errors will be caught and logged to stderr.

  Args:
    config_filenae: The filename of the config file to parse.
  
  Returns:
    A dictionary with {"user", "api_key"} keys parsed from the config file,
    or None if the credentials could not be parsed.
  """
  try:
    return parse_challonge_credentials_from_config(
        config_filename)
  except ConfigParser.Error as err:
    sys.stderr.write("Failed to read credentials from {0}: {1}.\n".format(
        config_filename, err))
    sys.stderr.write(
        "Check {0} for instructions on how to setup your config.\n".format(
        defaults.DEFAULT_CONFIG_FILENAME))
    return None


if __name__ == "__main__":
  if len(sys.argv) > 2:
    sys.stderr.write("Usage: {0} [<credentials_file>]\n".format(sys.argv[0]))
    sys.exit(1)
  
  if len(sys.argv) == 2:
    config_filename = sys.argv[1]
  else:
    config_filename = defaults.DEFAULT_CONFIG_FILENAME

  credentials = safe_parse_challonge_credentials_from_config(config_filename)
  if not credentials:
    sys.exit(1)
  else:
    print credentials

