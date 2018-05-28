# Challonge Tools

Contains various utility scripts that I use to make running Melee tournaments
easier.

# Shuffle Seeds

`shuffle_seeds.py`: Utilities for shuffling seeds in a tournament.

These functions help you shuffle a bracket while still preserving the projected
placement of each participant at the end of the tournament. This helps
randomize tournaments while still keeping things balanced.

### Examples

```
$ python shuffle_seeds.py 9
[1, 2, 3, 4, 6, 5, 8, 7, 9]
```

Returns the newly shuffled seeding order for a tournament with a given number
of participants. Each number indicates where the corresponding seed should be
listed.

```
$ python shuffle_seeds.py "Neal, Bryan, Paragon, gaR, Admiral Lightning Bolt, Eden"
['Neal', 'Bryan', 'Paragon', 'gaR', 'Eden', 'Admiral Lightning Bolt']
```

Returns the newly shuffled order of participants from a list of participant names.
Participants should be ordered from 1st seed to last seed. Leading and trailing
spaces in the participant names are stripped.

# Challonge Credentials Config

`parse_challonge_config.py`: Developer tool for getting Challonge credentials
from a config file.

The Challonge API key is something you want to keep secret. I set up this tool
so you can easily parse your Challonge info from a config file that can be
ignored from your git repo instead of hardcoding it into your code.

### Examples

See challonge.ini for an example config file with instructions.

```
$ python parse_challonge_config.py my_challonge.ini
{ user: 'blah', api_key: 'not telling' }
```
