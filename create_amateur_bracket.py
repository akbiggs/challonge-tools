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


# Global python & package imports.
import argparse
import challonge
import random
import sys
import urllib2

# Local imports.
import defaults
import puns
import util
import util_challonge

# Local from imports.
from shuffle_seeds import get_num_participants_placing_last


# Participant param names for requests.
_PARAMS_CHALLONGE_USERNAME = "challonge_username"
_PARAMS_SEED = "seed"
_PARAMS_NAME = "name"

# Credentials keys.
_CREDENTIALS_USER = "user"
_CREDENTIALS_API_KEY = "api_key"


def _get_participant_name(participant_info):
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


def _get_params_to_create_participant(participant_info,
                                      associate_challonge_account, seed):
  """Gets the params used to register a participant in a new tourney.

  Args:
    participant_info: Existing info on that participant grabbed from another
                      tourney.
    associate_challonge_account: Whether their Challonge account should be
                                 associated with their new registration. This
                                 will send them an email inviting them to the
                                 tourney.
    seed: The seed to give the participant.

  Returns:
    A dictionary that can be passed as params to challonge.participant.create
    to add the participant into a tourney.
  """
  params = {}
  params[_PARAMS_SEED] = seed
  params[_PARAMS_NAME] = _get_participant_name(participant_info)

  # Using a dash in 'challonge-username' instead of using
  # _PARAMS_CHALLONGE_USERNAME is intentional: dashes are used in
  # server responses while underscores are used in server requests (argh!!!)
  challonge_username = participant_info.get("challonge-username")
  if associate_challonge_account and challonge_username:
    params[_PARAMS_CHALLONGE_USERNAME] = challonge_username

  return params


def _get_losers_matches_determining_amateurs(matches, cutoff):
  """Filters existing matches that determine who qualifies for amateur's.

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


def _get_num_amateurs(num_participants, cutoff):
  """Figures out how many participants will be considered amateurs.

  Args:
    num_participants: The number of participants in the tournament.
    cutoff: The loser's round after which people are no longer qualified for
            amateur's bracket.

  Returns:
    The number of participants who will be classified as amateurs.
  """
  # Keep eliminating a loser's round worth of people until we've reached our
  # cutoff round. The number of eliminated people at that point is the number
  # of amateurs.
  num_amateurs = 0
  for losers_round in xrange(0, cutoff):
    num_eliminated = get_num_participants_placing_last(num_participants)

    num_amateurs = num_amateurs + num_eliminated
    num_participants = num_participants - num_eliminated

  return num_amateurs


# TODO: This main function is a mess, and totally won't make your life
# easy if you want to make a GUI out of this in the future. Clean up your act.
if __name__ == "__main__":
  argparser = argparse.ArgumentParser(description="Create amateur brackets.")
  argparser.add_argument("tourney_name",
                         help="the name of the tourney to create an amateur "
                              "bracket for")
  argparser.add_argument("--losers_round_cutoff",
                         type=int, default=2,
                         help="the loser's round after which people are no "
                              "longer qualified for amateur bracket")
  argparser.add_argument("--use_double_elimination",
                         type=util.str_to_bool, default=True,
                         help="whether the amateur bracket should use double "
                              "elimination or single elimination")
  argparser.add_argument("--config_file",
                         default=defaults.DEFAULT_CONFIG_FILENAME,
                         help="the config file to read your Challonge "
                              "credentials from")
  argparser.add_argument("--randomize_seeds",
                         type=util.str_to_bool, default=False,
                         help="whether the seeds should be randomized in the "
                              "amateur bracket. If this is off, the same "
                              "seeds from the main bracket will be used")
  argparser.add_argument("--associate_challonge_accounts",
                         type=util.str_to_bool, default=True,
                         help="whether challonge accounts should be "
                              "associated with the amateur bracket entrants. "
                              "This will invite their Challonge account to "
                              "the tourney via email, so use responsibly.")
  args = argparser.parse_args()

  # We need to initialize our Challonge credentials before we can
  # make any API calls.
  initialized = util_challonge.set_challonge_credentials_from_config(
      args.config_file)
  if not initialized:
    sys.exit(1)

  # Create the info for our amateur's bracket.
  tourney_name = util_challonge.parse_tourney_name(args.tourney_name)
  tourney_info = challonge.tournaments.show(tourney_name)
  tourney_title = tourney_info["name"]
  amateur_tourney_title = tourney_title + " Amateur's Bracket"
  amateur_tourney_name = tourney_name + "_amateur"
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

  # Get all decided loser's matches until the cutoff.
  cutoff = args.losers_round_cutoff
  matches = challonge.matches.index(tourney_name)
  amateur_deciding_matches = _get_losers_matches_determining_amateurs(
      matches, cutoff)
  num_completed_deciding_matches = sum(
      1 for x in amateur_deciding_matches if x["state"] == "complete")
  num_amateurs = _get_num_amateurs(tourney_info["participants-count"], cutoff)

  # If they're not all complete, we don't have enough info to create the
  # amateur bracket.
  if num_completed_deciding_matches != num_amateurs:
    sys.stderr.write(
        "There are still {0} matches incomplete before loser's round {1}.\n"
        "Please wait for these matches to complete before creating the\n"
        "amateur bracket.\n"
        "The last loser's round for amateur's qualification can be\n"
        "configured using the --losers_round_cutoff flag.\n".format(
            num_amateurs - num_completed_deciding_matches,
            cutoff + 1))
    sys.exit(1)

  # Gather up all the amateurs.
  amateur_ids = [match["loser-id"] for match in amateur_deciding_matches]
  amateur_infos = (
      challonge.participants.show(tourney_name, x) for x in amateur_ids)

  # Sort them based on seeding.
  if args.randomize_seeds:
    seed_fn = lambda x: random.random()
  else:
    seed_fn = lambda x: x[_PARAMS_SEED]
  amateur_infos = sorted(amateur_infos, key=seed_fn)

  all_amateur_params = [
      _get_params_to_create_participant(
          amateur_info,
          associate_challonge_account = args.associate_challonge_accounts,
          seed = (i + 1))
      for i, amateur_info in enumerate(amateur_infos)]

  # Confirm with the user that this is all okay.
  print "I creeped your tourney at http://challonge.com/{0}...".format(
      tourney_name)
  print ("Here's what I think the amateur bracket should look like, taking\n"
         "all people eliminated before Loser's Round {1}:".format(
             tourney_name, cutoff + 1))
  print
  print "Title: {0}".format(amateur_tourney_title)
  print "URL: {0}".format(amateur_tourney_url)
  print "Elimination Type: {0}".format(amateur_tourney_type)
  print
  print "Seeds:"
  need_to_send_at_least_one_email = any(
      x.get(_PARAMS_CHALLONGE_USERNAME) for x in all_amateur_params)
  if need_to_send_at_least_one_email:
    # I really don't want people accidentally sending email invites, so
    # we're very explicit about email invites and how to turn them off.
    print ("(to disable invites, use --associate_challonge_accounts=False)")
  for amateur_params in all_amateur_params:
    print "\t{0}. {1}".format(amateur_params[_PARAMS_SEED], 
                              amateur_params[_PARAMS_NAME])
    if amateur_params.get(_PARAMS_CHALLONGE_USERNAME):
      print "\t\t- Challonge account will receive email invite."
  print
  if not util.prompt_yes_no("Is it okay to create this amateur's bracket?"):
    print "Aw man. Alright, I'm not creating this amateur's bracket."
    print random.choice(puns.AMATEUR_PUNS)
    print ("( Feel free to report bugs and request features at "
           "https://github.com/akbiggs/challonge-tools/issues )")
    sys.exit(1)

  # We've got confirmation. Go ahead and create the amateur bracket.
  challonge.tournaments.create(amateur_tourney_title, amateur_tourney_name,
                               amateur_tourney_type)
  for amateur_params in all_amateur_params:
    challonge.participants.create(amateur_tourney_name, **amateur_params)

  print "Created {0} at {1}.".format(amateur_tourney_title,
                                     amateur_tourney_url)
  print "Start the amateur bracket at the above URL when you're ready!"
