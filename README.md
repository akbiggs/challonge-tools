# Challonge Tools

Contains various utility scripts that I use to make running
[Challonge](http://challonge.com) tournaments easier (specifically
for Super Smash Bros. Melee).

All examples are assumed to be run from a downloaded version of this
repository.

# Running Scripts

```
git clone https://github.com/akbiggs/challonge-tools
cd challonge-tools
python <script_to_run>
```

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

# Amateur Bracket Creator

`create_amateur_bracket.py`: Creates an amateur tournament automatically from
an existing Challonge tournament.

An amateur tournament takes people who place below a certain threshold and
hosts a separate tournament for them after the main tournament. This helps
people get more practice and have more fun, especially in a game with a
soul-crushing learning curve like Melee.

### Prerequisites

1. Install pychallonge dependencies: `pip install iso8601 # required 
   for pychallonge`
2. Install pychallonge locally: `pip install -e 
   git+http://github.com/russ-/pychallonge#egg=pychallonge --user` 
3. Edit [challonge.ini](https://github.com/akbiggs/challonge-tools/blob/master/challonge.ini)
   with your Challonge username and [API key](https://challonge.com/settings/developer).

### Examples

`$ python create_amateur_bracket.py mtvmelee72`

Examines [http://challonge.com/mtvmelee72](http://challonge.com/mtvmelee72)
and offers to create an amateur bracket using the people eliminated in
Loser's Rounds 1 and 2.

The tool will get your approval before it creates anything, and it won't do
anything if an amateur bracket already exists. It won't modify your existing
tournament's data.

Here's an example session where I
[approved creating the amateur bracket](https://pastebin.com/LTfCKFWr), and
here's a session where I [rejected creating it](https://pastebin.com/qDvP8Ayz).
If I try to create an amateur bracket that already exists, [the script doesn't
do anything](https://pastebin.com/FiEb4ejS).

**Flags:**

* `--use_double_elimination=True`: Whether the amateur bracket should use
  double-elimination or single-elimination. Default: `True`
* `--randomize_seeds=False`: Whether the amateur bracket should completely
  randomize the seeds or use the seeding from the main bracket to figure
  them out. Default: `False`
* `--losers_round_cutoff=2`: The loser's round after which people who
  are eliminated no longer qualify for the amateur bracket. A value of
  2 means that Loser's Rounds 1 and 2 are included, but not Loser's Round 3.
  Default: `2`
* `--associate_challonge_accounts=True`: Whether the users' Challonge accounts
  should be associated with their entries in the amateur brackets. This is
  useful to help them track all the tournaments they've entered, but it also
  makes the amateur bracket send an email to them, so use responsibly when
  generating amateur brackets. The tool will let you know if their account
  will be emailed.
* `--config_file="challonge.ini"`: The config file to read your Challonge
  API key and username from. Needs to be edited before running Default: `"challonge.ini"`

e.g.

```
$ python create_amateur_bracket.py mtvmelee72 \
      --config_file=akbiggs_challonge.ini \
      --use_double_elimination=False \
```

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
