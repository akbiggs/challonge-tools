import json
import os
from os.path import dirname, abspath
import pytest
import random
import sys
from unittest.mock import Mock

# Add the parent directory to the path
CWD = dirname(abspath(__file__))
sys.path.append(dirname(CWD))

import garpr_seeds


def rankings(region):
    test_file = os.path.join(CWD, 'test_data',
                             '{}_rankings.json'.format(region))
    with open(test_file) as data:
        return json.load(data)['ranking']


@pytest.fixture(scope='session', autouse=True)
def mock_garpr_request():
    garpr_seeds._fetch_garpr_rankings = Mock(return_value=rankings('norcal'))
    yield


@pytest.fixture
def players():
    return ['Umarth', 'trock', 'NMW']


def seed_players(players):
    """Given a list of tags, return their seeds."""
    rankings = garpr_seeds.get_garpr_ranks(players, '')
    return garpr_seeds.ranks_to_seeds(rankings)


def test_seeding_order(players):
    """Verify the output of ranking to seeding."""
    seeds = seed_players(players)

    assert seeds == [2, 3, 1]


def test_give_last_seed_to_unknown(players):
    """Players not on gaR PR should be seeded last."""
    players.append('BLAHBLAHBLAHBLAH')
    seeds = seed_players(players)

    assert seeds == [2, 3, 1, 4]


def test_seed_unknowns_in_order(players):
    """Unknown players are seeded in the order they are encountered."""
    players.insert(2, 'BLAHBLAH')
    players.append('BLAHBLAHBLAHBLAH')

    seeds = seed_players(players)

    assert seeds == [2, 3, 4, 1, 5]


def random_case(text):
    choice = random.choice
    return ''.join(getattr(c, choice(['lower', 'upper']))() for c in text)


def test_ignore_case(players):
    """Ignore case when getting seeds."""
    pLayERs = map(random_case, players)
    seeds = seed_players(pLayERs)

    assert seeds == [2, 3, 1]


def test_multiple_tags_slash(players):
    """Players can have multiple tags, denoted by a '/' or '()'."""
    players.append('jubby')
    players.append('darkwizard123')
    players.append('dragonslayer69')
    seeds = seed_players(players)

    assert seeds == [2, 3, 1, 6, 4, 4]


def test_multiple_tags_parens(players):
    """Players can have multiple tags, denoted by a '/' or '()'."""
    garpr_seeds._fetch_garpr_rankings = Mock(return_value=rankings('googlemtv'))
    players = ['bryan', 'yellow yoshi', 'gar', 'char', 'twig']
    seeds = seed_players(players)

    assert seeds == [2, 3, 1, 3, 5]
