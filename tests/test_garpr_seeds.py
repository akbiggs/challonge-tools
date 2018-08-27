import json
import os
from os.path import dirname, abspath
import pytest
import sys
from unittest.mock import Mock

# Add the parent directory to the path
sys.path.append(dirname(dirname(abspath(__file__))))

import garpr_seeds


def norcal_rankings():
    NORCAL = os.path.join('test_data', 'norcal_rankings.json')
    with open(NORCAL) as data:
        return json.load(data)['ranking']


@pytest.fixture(scope='session', autouse=True)
def mock_garpr_request():
    garpr_seeds._fetch_garpr_rankings = Mock(return_value=norcal_rankings())
    yield


@pytest.fixture
def players():
    return ['NMW', 'Umarth', 'trock']


def test_seeding_order(players):
    """Verify the output of ranking to seeding."""
    rankings = garpr_seeds.get_garpr_ranks(players, 'norcal')
    seeds = garpr_seeds.ranks_to_seeds(rankings)

    assert seeds == [1, 2, 3]


def test_give_last_seed_to_unknown(players):
    """Players not on gaR PR should be seeded last."""
    players.append('BLAHBLAHBLAHBLAH')
    rankings = garpr_seeds.get_garpr_ranks(players, 'norcal')
    seeds = garpr_seeds.ranks_to_seeds(rankings)

    assert seeds == [1, 2, 3, 4]
