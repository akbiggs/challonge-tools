# Challonge Tools

Contains various utility scripts that I use to make running
[Challonge](http://challonge.com) tournaments easier (specifically
for Super Smash Bros. Melee).

All examples are assumed to be run from a downloaded version of this
repository.

# Example workflow

```
# After creating a local tourney at https://challonge.com/mtvmelee77,
# I want to seed participants based on their Google MTV gaR PR rankings, and shuffle
# the bracket a bit while preserving each participant's projected placement.
python3 garpr_seeds_challonge.py mtvmelee77 --shuffle --region=googlemtv

# Then later on in the local, after loser's round 2 has finished, I want
# to create an amateur bracket automatically, so I don't have to spend time
# manually entering in each participant.
python3 create_amateur_bracket.py mtvmelee77

# Once that amateur bracket is created, it's available at
# https://challonge.com/mtvmelee77_amateur. The amateur bracket will use the
# same seedings as the original bracket by default, but I want to vary up the
# matches, so I run shuffled gaR PR seeds on the bracket again.
python3 garpr_seeds_challonge.py mtvmelee77_amateur --shuffle --region=googlemtv
```

# Index

* [Get Started](https://github.com/akbiggs/challonge-tools#get-started)
* [gaR PR Seeds (with Challonge)](https://github.com/akbiggs/challonge-tools#gar-pr-seeds-with-challonge)
* [gaR PR Seeds (without Challonge)](https://github.com/akbiggs/challonge-tools#gar-pr-seeds-without-challonge)
* [Shuffle Seeds (with Challonge)](https://github.com/akbiggs/challonge-tools#shuffle-seeds-with-challonge)
* [Shuffle Seeds (without Challonge)](https://github.com/akbiggs/challonge-tools#shuffle-seeds-without-challonge)
* [Amateur Bracket Creator](https://github.com/akbiggs/challonge-tools#amateur-bracket-creator)
* [Challonge Credentials Config](https://github.com/akbiggs/challonge-tools#challonge-credentials-config)
* [Running Tests](https://github.com/akbiggs/challonge-tools#running-tests)

# Get Started

These scripts use [Python 3](https://www.python.org/downloads/), and are incompatible
with Python 2. If you run into any issues setting this up, feel free to [open
up a new issue here](https://github.com/akbiggs/challonge-tools/issues).

1. Clone and enter the repository from your terminal using Git.

```
git clone https://github.com/akbiggs/challonge-tools
cd challonge-tools
```

2. **(Recommended):** Create and activate a new Python virtual environment.
This will help ensure that your environment is configured correctly.

```
python3 -m venv challonge_tools_env
source challonge_tools_env/bin/activate
```

3. Install python package dependencies.

```
pip install -r requirements.txt
```

4. Edit your local copy of [challonge.ini](https://github.com/akbiggs/challonge-tools/blob/master/challonge.ini)
   with your Challonge username and [API key](https://challonge.com/settings/developer).

5. Run the script you want to try!

```
python3 <script_to_run>.py
```

# gaR PR Seeds (with Challonge)

`garpr_seeds_challonge.py`: Seeds a tourney based on
[gaR PR](http://www.garpr.com) rankings.

Any unrecognized names will be seeded in last-place (in order of their
original appearance in the seeding list). Case is ignored in names.

### Examples

```
$ python3 garpr_seeds_challonge.py 32w50dxc
Tournament updated; see seeds at http://challonge.com/32w50dxc/participants.
```

You can change the region using the `--region` flag.

```
$ python3 garpr_seeds_challonge.py 32w50dxc --region=googlemtv
Tournament updated; see seeds at http://challonge.com/32w50dxc/participants.
```

Flags:

* `--region=googlemtv`: The region being used to get gaR PR rankings. Default:
  `googlemtv`
* `--print_only=False`: Set this to `True` if you just want to print out the
  new seeds without committing them to the tournament. This is useful for
  testing before you reseed your tournament. Default: `False`
* `--shuffle=False`: Set this to `True` if you want to shuffle the seeds
  afterwards while still preserving each participant's projected placement.
  This helps to introduce a bit of variance into the bracket. Default: `False`
* `--config_file=challonge.ini`: The config file to read your Challonge
  credentials from. This is useful to reduce the risk of accidentally
  committing your credentials to source control. Default: `challonge.ini`

# gaR PR Seeds (without Challonge)

`garpr_seeds.py`: Gets seeds without using the Challonge API.

Useful for testing out the rankings without an actual tournament.

### Examples

```
$ python3 garpr_seeds.py "Eden, Bryan, Non-gaR PR Person, Admiral"
[3, 2, 4, 1]
```

# Shuffle Seeds (with Challonge)

`shuffle_seeds_challonge.py`: Shuffles seeds in a Challonge tournament.

These functions help you shuffle a bracket while still preserving the projected
placement of each participant at the end of the tournament. This helps
randomize tournaments while still keeping things balanced, compared to
Challonge's "shuffle seeds", which just randomizes everything.

### Example

```
$ python3 shuffle_seeds_challonge.py zcmvlkxm
Seeds shuffled: http://challonge.com/zcmvlkxm/participants
```

Automatically updates the seeding of all participants based on a generated
shuffle order.

**Flags:**

* `--config_file=challonge.ini`: The config file to read your Challonge
  credentials from. This is useful to reduce the risk of accidentally
  committing your credentials to source control. Default: `challonge.ini`

# Shuffle Seeds (without Challonge)

`shuffle_seeds.py`: Shuffles seeds without using the Challonge API.

This is useful when you don't have access to an internet connection, or
when you just want to test out the randomization.

### Examples

```
$ python3 shuffle_seeds.py 9
[1, 2, 3, 4, 6, 5, 8, 7, 9]
```

Returns the newly shuffled seeding order for a tournament with a given number
of participants. Each number indicates where the corresponding seed should be
listed.

```
$ python3 shuffle_seeds.py "Neal, Bryan, Paragon, gaR, Admiral Lightning Bolt, Eden"
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

### Examples

```
$ python3 create_amateur_bracket.py mtvmelee72
```

Examines [http://challonge.com/mtvmelee72](http://challonge.com/mtvmelee72)
and offers to create an amateur bracket using the people eliminated in
Loser's Rounds 1 and 2.

The tool will get your approval before it creates anything, and it won't do
anything if an amateur bracket already exists. It won't modify your existing
tournament's data.

Example sessions with this tool:

1. [Approved creating an amateur bracket](https://pastebin.com/LTfCKFWr)
2. [Rejecting the amateur bracket instead](https://pastebin.com/qDvP8Ayz)
3. [The tool won't damage anything that already
   exists](https://pastebin.com/FiEb4ejS)
4. [The tool lets you know if you're creating the amateur bracket
   too early](https://pastebin.com/AazXDi84)

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
* `--associate_challonge_accounts=False`: Whether the users' Challonge accounts
  should be associated with their entries in the amateur brackets. This is
  useful to help them track all the tournaments they've entered, but it also
  makes the amateur bracket send an email to them, so use responsibly when
  generating amateur brackets. The tool will let you know if their account
  will be emailed. Default: `False`
* `--config_file="challonge.ini"`: The config file to read your Challonge
  API key and username from. Default: `"challonge.ini"`

e.g.

```
$ python3 create_amateur_bracket.py mtvmelee72 \
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
$ python3 parse_challonge_config.py my_challonge.ini
{ user: 'blah', api_key: 'not telling' }
```

# Running Tests

Before running the tests, you will need to initialize
[Bats](https://github.com/sstephenson/bats):

```
git submodule update --init --recursive
```

Afterwards, just run `test.sh` to run all the unit tests:

```
./test.sh
```
