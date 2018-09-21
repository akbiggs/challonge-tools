#!/usr/bin/env python3


"""Creates an amateur tournament from an existing Challonge tournament.

An amateur tournament takes people who place below a certain threshold and
hosts a separate tournament for them after the main tournament. This helps
people get more practice and have more fun, especially in a game with a
soul-crushing learning curve like Melee.

Examples:

  1. python create_amateur_bracket.py <my_tournament_name>

Examines your tourney and offers to create an amateur bracket using
the people eliminated in Loser's Rounds 1 and 2. "name" refers to the
unique string identifying your tournament in the challonge.com URL, e.g.
for http://challonge.com/mtvmelee72 it would be "mtvmelee72".

  2. python create_amateur_bracket.py <my_tournament_name> \
         --single_elimination

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


class AmateurBracketAlreadyExists(Exception):
    """An amateur bracket already exists for this tournament."""


class MainTournamentNotFarEnoughAlong(Exception):
    """Not enough loser's matches are completed to create an amateur bracket."""
    def __init__(self, message):
        super().__init__(message)
        self.matches_remaining = None


def _get_params_to_create_participant(
        participant_info, associate_challonge_account, seed):
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
    params[_PARAMS_NAME] = util_challonge.get_participant_name(participant_info)

    challonge_username = participant_info.get(_PARAMS_CHALLONGE_USERNAME)
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
    return [x for x in matches if -cutoff <= x["round"] and x["round"] <= -1]


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
    for _ in range(cutoff):
        num_eliminated = get_num_participants_placing_last(num_participants)

        num_amateurs += num_eliminated
        num_participants -= num_eliminated

    return num_amateurs

def get_amateur_participants(tourney_name, amateur_deciding_matches):
    """
    Get a the players eligible for the amateur bracket.

    @params tourney_name: name of the tourney.
    @params amateur_deciding_matches: matches that feed into the amateur
        bracket.
    @returns: list of players.
    @raises MainTournamentNotFarEnoughAlong: iff main bracket still has matches
        that need to be completed.

    """
    amateur_infos = []
    for match in amateur_deciding_matches:
        if match["state"] == "complete":
            id = match["loser_id"]
            player = challonge.participants.show(tourney_name, id)
        elif match["state"] == "open":
            # If the match isn't complete, create a frankenplayer by
            # combining the two players' tags and averaging their seed.
            id1 = match["player1_id"]
            id2 = match["player2_id"]
            player1 = challonge.participants.show(tourney_name, id1)
            player2 = challonge.participants.show(tourney_name, id2)

            player = player1
            player[_PARAMS_SEED] = (player1[_PARAMS_SEED] +
                                    player2[_PARAMS_SEED]) // 2
            player['display_name'] = '{} / {}'.format(player1['display_name'],
                                                      player2['display_name'])
            player[_PARAMS_CHALLONGE_USERNAME] = None
        else:
            # We can't create an amateur bracket if any of the loser's matches'
            # state is 'pending'.
            num_pending_matches = sum(
                1 for x in amateur_deciding_matches if x["state"] == "pending"
            )
            err = MainTournamentNotFarEnoughAlong(
                "Some loser's bracket matches don't have two players in them "
                "yet. Cannot create amateur bracket.")
            err.matches_remaining = num_pending_matches
            raise err

        amateur_infos.append(player)
    return amateur_infos


def create_amateur_bracket(tourney_url, single_elimination,
                           losers_round_cutoff, randomize_seeds,
                           associate_challonge_accounts=False,
                           incomplete=False, interactive=False):
    """
    Create the amateur bracket.

    Most of the params are the same as their argparse counterpart.

    @param interactive: If this is being run on the command line and can take
        user input.

    @returns: URL of the generated amateur bracket.

    """
    # Create the info for our amateur's bracket.
    tourney_name = util_challonge.extract_tourney_name(tourney_url)
    tourney_info = challonge.tournaments.show(tourney_name)
    tourney_title = tourney_info["name"]
    amateur_tourney_title = tourney_title + " Amateur's Bracket"
    amateur_tourney_name = tourney_name + "_amateur"
    amateur_tourney_url = util_challonge.tourney_name_to_url(amateur_tourney_name)
    if single_elimination:
        amateur_tourney_type = "single elimination"
    else:
        amateur_tourney_type = "double elimination"

    # Make sure the tournament doesn't already exist.
    existing_amateur_tournament = util_challonge.get_tourney_info(amateur_tourney_name)
    if existing_amateur_tournament:
        raise AmateurBracketAlreadyExists(
            "Amateur tournament already exists at {}."
            .format(amateur_tourney_url))

    # Get all decided loser's matches until the cutoff.
    cutoff = losers_round_cutoff
    matches = challonge.matches.index(tourney_name)
    amateur_deciding_matches = _get_losers_matches_determining_amateurs(matches, cutoff)
    num_completed_deciding_matches = sum(
        1 for x in amateur_deciding_matches if x["state"] == "complete"
    )
    num_amateurs = _get_num_amateurs(tourney_info["participants_count"], cutoff)

    # If they're not all complete, we don't have enough info to create the
    # amateur bracket.
    if num_completed_deciding_matches != num_amateurs:
        err = MainTournamentNotFarEnoughAlong(
            "There are still {0} matches incomplete before loser's round {1}.\n"
            "Please wait for these matches to complete before creating the\n"
            "amateur bracket.\n"
            "The last loser's round for amateur's qualification can be\n"
            "configured using the --losers_round_cutoff flag.\n".format(
                num_amateurs - num_completed_deciding_matches, cutoff + 1
            )
        )
        err.matches_remaining = num_amateurs - num_completed_deciding_matches

        if interactive:
            print(err)

            if not incomplete:
                print("Alternatively, we can 'approximate' the amateur\n"
                      "bracket if you pass in the --incomplete flag.")
                sys.exit()
            else:
                if not util.prompt_yes_no("Create amateur bracket anyway?"):
                    sys.exit()

        elif not incomplete:
            raise err

    # Gather up all the amateurs.
    amateur_infos = get_amateur_participants(tourney_name,
                                             amateur_deciding_matches)

    # Sort them based on seeding.
    if randomize_seeds:
        seed_fn = lambda x: random.random()
    else:
        seed_fn = lambda x: x[_PARAMS_SEED]
    amateur_infos = sorted(amateur_infos, key=seed_fn)

    all_amateur_params = [
        _get_params_to_create_participant(
            amateur_info,
            associate_challonge_account=associate_challonge_accounts,
            seed=i
        )
        for i, amateur_info in enumerate(amateur_infos, 1)
    ]

    if interactive:
        # Confirm with the user that this is all okay.
        print("I creeped your tourney at {0}...".format(tourney_name))
        print(
            (
                "Here's what I think the amateur bracket should look like, taking\n"
                "all people eliminated before Loser's Round {0}:".format(cutoff + 1)
            )
        )
        print()
        print("Title: {0}".format(amateur_tourney_title))
        print("URL: {0}".format(amateur_tourney_url))
        print("Elimination Type: {0}".format(amateur_tourney_type))
        print()
        print("Seeds:")
        need_to_send_at_least_one_invite = any(
            x.get(_PARAMS_CHALLONGE_USERNAME) for x in all_amateur_params
        )
        if need_to_send_at_least_one_invite:
            # I really don't want people accidentally sending email invites, so
            # we're very explicit about email invites and how to turn them off.
            print("(to disable invites, use --associate_challonge_accounts=False)")
        for amateur_params in all_amateur_params:
            print(
                "\t{0}. {1}".format(
                    amateur_params[_PARAMS_SEED], amateur_params[_PARAMS_NAME]
                )
            )
            if amateur_params.get(_PARAMS_CHALLONGE_USERNAME):
                print("\t\t- Challonge account will receive email invite.")
        print()
        if not util.prompt_yes_no("Is it okay to create this amateur's bracket?"):
            print("Aw man. Alright, I'm not creating this amateur's bracket.")
            print(random.choice(puns.AMATEUR_PUNS))
            print(
                "( Feel free to report bugs and request features at "
                "https://github.com/akbiggs/challonge-tools/issues )"
            )
            sys.exit(1)

    # We've got confirmation. Go ahead and create the amateur bracket.
    tourney, subdomain = util_challonge.tourney_name_to_parts(amateur_tourney_name)
    challonge.tournaments.create(
        amateur_tourney_title, tourney, amateur_tourney_type,
        subdomain=subdomain)

    for amateur_params in all_amateur_params:
        challonge.participants.create(amateur_tourney_name, **amateur_params)

    if interactive:
        print("Created {0} at {1}.".format(amateur_tourney_title, amateur_tourney_url))
        print("Start the amateur bracket at the above URL when you're ready!")

    return amateur_tourney_url

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description="Create amateur brackets.",
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(
        "tourney_url",
        help="the URL of the tourney to create an amateur bracket for",
    )
    argparser.add_argument(
        "--losers_round_cutoff",
        type=int,
        default=2,
        help="the loser's round after which people are no "
        "longer qualified for amateur bracket",
    )
    argparser.add_argument(
        "--single_elimination",
        action="store_true",
        help="use single elimination for the amateur bracket",
    )
    argparser.add_argument(
        "--config_file",
        default=defaults.DEFAULT_CONFIG_FILENAME,
        help="the config file to read your Challonge " "credentials from",
    )
    argparser.add_argument(
        "--randomize_seeds",
        action="store_true",
        help="whether the seeds should be randomized in the "
        "amateur bracket. If this is off, the same "
        "seeds from the main bracket will be used",
    )
    argparser.add_argument(
        "--incomplete",
        action="store_true",
        help="create the amateur bracket before the main bracket has "
        "fully completed."
    )
    argparser.add_argument(
        "--associate_challonge_accounts",
        action="store_true",
        help="whether challonge accounts should be "
        "associated with the amateur bracket entrants. "
        "This will invite their Challonge account to "
        "the tourney via email, so use responsibly.",
    )
    args = argparser.parse_args()

    # We need to initialize our Challonge credentials before we can
    # make any API calls.
    initialized = util_challonge.set_challonge_credentials_from_config(args.config_file)
    if not initialized:
        sys.exit(1)

    try:
        create_amateur_bracket(
            args.tourney_url,
            single_elimination=args.single_elimination,
            losers_round_cutoff=args.losers_round_cutoff,
            randomize_seeds=args.randomize_seeds,
            associate_challonge_accounts=args.associate_challonge_accounts,
            incomplete=args.incomplete,
            interactive=True
        )
    except (AmateurBracketAlreadyExists, MainTournamentNotFarEnoughAlong) as e:
        print(e)
