from os.path import dirname, abspath
import pytest
import sys

# Add the parent directory to the path
CWD = dirname(abspath(__file__))
sys.path.append(dirname(CWD))

import util_challonge


@pytest.mark.parametrize('url, expected', [
    ('https://challonge.com/mtvmelee82', 'mtvmelee82'),
    ('challonge.com/mtvmelee82', 'mtvmelee82'),
    ('http://challonge.com/mtvmelee82_amateur', 'mtvmelee82_amateur'),
    ('https://mtvmelee.challonge.com/mtvmelee84', 'mtvmelee-mtvmelee84'),
    ('mtvmelee.challonge.com/mtvmelee84/participants', 'mtvmelee-mtvmelee84'),
    ('mtvmelee.challonge.com/mtvmelee84', 'mtvmelee-mtvmelee84'),
    ('https://mtvmelee.challonge.com/mtvmelee84_amateur', 'mtvmelee-mtvmelee84_amateur'),
    ('mtvmelee69', ValueError),
])
def test_extract_tourney_name(url, expected):
    """Extract the Challonge tourney name from URL."""
    try:
        assert util_challonge.extract_tourney_name(url) == expected
    except ValueError as e:
        if expected != ValueError:
            raise e
