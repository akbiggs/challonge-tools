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


def norcal_rankings():
    NORCAL = os.path.join(CWD, 'test_data', 'norcal_rankings.json')
    with open(NORCAL) as data:
        return json.load(data)['ranking']


@pytest.fixture(scope='session', autouse=True)
def mock_garpr_request():
    garpr_seeds._fetch_garpr_rankings = Mock(return_value=norcal_rankings())
    yield


@pytest.fixture
def players():
    return ['NMW', 'Umarth', 'trock']


def seed_players(players):
    rankings = garpr_seeds.get_garpr_ranks(players, 'norcal')
    return garpr_seeds.ranks_to_seeds(rankings)


def test_seeding_order(players):
    """Verify the output of ranking to seeding."""
    seeds = seed_players(players)

    assert seeds == [1, 2, 3]


def test_give_last_seed_to_unknown(players):
    """Players not on gaR PR should be seeded last."""
    players.append('BLAHBLAHBLAHBLAH')
    seeds = seed_players(players)

    assert seeds == [1, 2, 3, 4]


def test_seed_unknowns_in_order(players):
    """Unknown players are seeded in the order they are encountered."""
    players.append('BLAHBLAHBLAHBLAH')
    players.insert(2, 'BLAHBLAH')

    seeds = seed_players(players)

    assert seeds == [1, 2, 4, 3, 5]


def random_case(text):
    """Forgive me, father, for I have sinned."""
    return ''.join(getattr(c, random.choice(['lower', 'upper']))()
                   for c in text)


def test_ignore_case(players):
    """Ignore case when getting seeds."""
    pLayERs = map(random_case, players)
    seeds = seed_players(pLayERs)

    assert seeds == [1, 2, 3]
