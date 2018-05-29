#!/usr/bin/env python

"""Creates an amateur tournament from an existing Challonge tournament.

An amateur tournament takes people who place below a certain threshold and
hosts a separate tournament for them after the main tournament. This helps
people get more practice and have more fun, especially in a game with a
soul-crushing learning curve like Melee.

Prerequisites:

  1. pip install iso8601 # required for challongepy
  2. pip install -e git+http://github.com/russ-/pychallonge#egg=pychallonge \
         --user 
  3. Setup your challonge.ini with your API key and username.

Examples:

  1. python create_amateur_bracket.py <my_tournament_name>

Examines your tourney and offers to create an amateur bracket using
the people eliminated in Loser's Rounds 1 and 2. "name" refers to the
unique string identifying your tournament in the challonge.com URL, e.g.
for http://challonge.com/mtvmelee72 it would be "mtvmelee72".

  2. python create_amateur_bracket.py <my_tournament_name> \
         --use_double_elimination=False

Offers to create an amateur bracket with single elimination.

  3. python create_amateur_bracket.py <my_tournament_name> \
         --randomize_seeds=False

Offers to create an amateur bracket where the seeds are picked randomly.

  4. python create_amateur_bracket.py <my_tournament_name> \
         --config_file=my_challonge.ini

Configures your Challonge credentials from a custom config file. This is
useful for hiding your credentials from version control. See "challonge.ini"
for an example config file with instructions.
"""

import argparse
import challonge
import random
import sys
import urllib2

import defaults
from parse_challonge_credentials import safe_parse_challonge_credentials_from_config


def _set_challonge_credentials_from_config(config_filename):
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


def _get_matches_determining_amateurs(matches, cutoff):
  """Filters the matches that determine who qualifies for amateur's bracket.

  Args:
    matches: A list of Challonge matches retrieved from the Challonge API.
    cutoff: The loser's round after which people are no longer qualified for
            amateur's bracket.

  Returns:
    A list of all matches that determine the amateur's bracket.
  """
  # Loser's round 1 is -1, loser's round 2 is -2, etc.
  # So if our cutoff is at loser's round 3, we want all matches in
  # the range [-3, -1], since these are all matches that will eliminate
  # someone into amateur's bracket.
  cutoff = args.losers_round_cutoff
  return [
      x for x in matches if -cutoff <= x["round"] and x["round"] <= -1]


def _str_to_bool(s):
  """Converts a string value to a boolean value.

  Args:
    s: The string to convert to a boolean value.

  Raises:
    argparse.ArgumentTypeError: If the string doesn't correspond to a bool.

  Returns:
    The corresponding boolean value for the string.
  """
  if s.lower() in ('yes', 'true', 't', 'y', '1'):
    return True
  elif s.lower() in ('no', 'false', 'f', 'n', '0'):
    return False
  else:
    raise argparse.ArgumentTypeError('Boolean value expected.')


def _prompt_yes_no(prompt):
  """Prompts the user to respond yes/no to a question.
  
  Asks repeatedly until valid input is given.

  Args:
    prompt: The prompt to use. This should not include "[y/n]".

  Returns:
    True if the user answered yes, False if they answered yes.
  """
  while True:
    print (prompt + " [y/n]"),

    choice = raw_input().lower()
    try:
      return _str_to_bool(choice)
    except argparse.ArgumentTypeError:
      print "Invalid response. Please say 'y' or 'n'."


if __name__ == "__main__":
  argparser = argparse.ArgumentParser(description="Create amateur brackets.")
  argparser.add_argument("tourney_name", type=str,
                         help="the name of the tourney to create an amateur "
                              "bracket for")
  argparser.add_argument("--losers_round_cutoff", type=int,
                         default=2,
                         help="the loser's round after which people are no "
                              "longer qualified for amateur bracket")
  argparser.add_argument("--use_double_elimination", type=_str_to_bool,
                         default=True,
                         help="whether the amateur bracket should use double "
                              "elimination or single elimination")
  argparser.add_argument("--config_file",
                         default=defaults.DEFAULT_CONFIG_FILENAME,
                         help="the config file to read your Challonge "
                              "credentials from")
  argparser.add_argument("--randomize_seeds", type=_str_to_bool,
                         default=False,
                         help="whether the seeds should be randomized in the "
                              "amateur bracket. If this is off, the same "
                              "seeds from the main bracket will be used")
  args = argparser.parse_args()

  # We need to initialize our Challonge credentials before we can
  # make any API calls.
  initialized = _set_challonge_credentials_from_config(args.config_file)
  if not initialized:
    sys.stderr.write("Could not initialize Challonge API.\n")
    sys.stderr.write("Have you filled in the 'user' and 'api_key' values in "
                     "{0}?\n".format(args.config_file))
    sys.exit(1)

  # Create the info for our amateur's bracket.
  tourney_name = args.tourney_name.split("http://challonge.com/")[0]
  tourney_title = challonge.tournaments.show(args.tourney_name)["name"]
  amateur_tourney_title = tourney_title + " Amateur's Bracket"
  amateur_tourney_name = args.tourney_name + "_amateur"
  amateur_tourney_url = "http://challonge.com/{0}".format(
      amateur_tourney_name)
  if args.use_double_elimination:
    amateur_tourney_type = "double elimination"
  else:
    amateur_tourney_type = "single elimination"

  # This bit is ugly... we check that there's no existing amateur bracket
  # for this tournament by getting a 404 from trying to fetch the URL we'll
  # use for the amateur bracket. As far as I can tell, there's no nicer way
  # to check if the bracket already exists with the Challonge API wrapper
  # we're using.
  existing_amateur_tournament = None
  try:
    existing_amateur_tournament = challonge.tournaments.show(
        amateur_tourney_name)
  except urllib2.HTTPError as err:
    # If we got a 404, we queried fine and no amateur bracket exists,
    # but otherwise we've got an unexpected error, so we escalate it.
    if err.code != 404:
      raise err

  if existing_amateur_tournament:
    sys.stderr.write("Amateur tournament already exists at "
                     "{0}.\n".format(amateur_tourney_url))
    sys.exit(1)

  # Get all loser's matches until the cutoff, and verify that they're
  # complete so we have enough info to create the amateur's bracket.
  cutoff = args.losers_round_cutoff
  matches = challonge.matches.index(args.tourney_name)
  amateur_deciding_matches = _get_matches_determining_amateurs(matches, cutoff)
  if any(x["state"] != "complete" for x in amateur_deciding_matches):
    sys.stderr.write("There are still matches underway before loser's "
                     "round {0}. Please wait for these matches to complete "
                     "before creating the amateur bracket. The loser's "
                     "round to cutoff for amateur's can be configured using "
                     "the --losers_round_cutoff flag.\n".format(cutoff + 1))
    sys.exit(1)

  # Gather up all the amateurs.
  amateur_ids = [match["loser-id"] for match in amateur_deciding_matches]
  amateur_infos = (
      challonge.participants.show(args.tourney_name, x) for x in amateur_ids)

  # Sort them based on seeding.
  if args.randomize_seeds:
    sort_fn = lambda x: random.random()
  else:
    sort_fn = lambda x: x["seed"]
  amateur_infos = sorted(amateur_infos, key=sort_fn)

  # Confirm with the user that this is all okay.
  print "I creeped your tourney at http://challonge.com/{0}...".format(
      args.tourney_name)
  print ("Here's what I think the amateur bracket should look like, taking\n"
         "all people eliminated before Loser's Round {1}:".format(
             args.tourney_name, cutoff + 1))
  print
  print "Title: {0}".format(amateur_tourney_title)
  print "URL: {0}".format(amateur_tourney_url)
  print "Elimination Type: {0}".format(amateur_tourney_type)
  print
  print "Seeds:"
  for i, amateur_info in enumerate(amateur_infos):
    print "\t{0}. {1}".format(i + 1, amateur_info["name"])
  print
  confirmed = _prompt_yes_no("Is it okay to create this amateur's bracket?")

  if not confirmed:
    print "Aw man. Alright, I'm not creating this amateur's bracket."
    print "Talk about an amateur move..."
    print ("( Feel free to report bugs and request features at "
           "https://github.com/akbiggs/challonge-tools/issues )")
    sys.exit(1)

  # We've got confirmation. Go ahead and create the amateur bracket.
  challonge.tournaments.create(amateur_tourney_title, amateur_tourney_name,
                               amateur_tourney_type)
  for i, amateur_info in enumerate(amateur_infos):
    challonge.participants.create(amateur_tourney_name, amateur_info["name"],
                                  seed=(i + 1))

  print "Created {0} at {1}.".format(amateur_tourney_title,
                                     amateur_tourney_url)
