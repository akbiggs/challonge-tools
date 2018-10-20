#!/usr/bin/env python
"""
This is a webapp written in Flask to access the Challonge tools backend,
and make it easier for the average user to use.

"""
import challonge
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, request, flash, session,\
                  url_for
from flask_sslify import SSLify
import os
from os.path import dirname, abspath
import re
from requests.exceptions import HTTPError

from create_amateur_bracket import AmateurBracketAlreadyExistsError
from create_amateur_bracket import AmateurBracketRequiredMatchesIncompleteError
from create_amateur_bracket import create_amateur_bracket
import garpr_seeds_challonge


app = Flask(__name__)
sslify = SSLify(app)
app.url_map.strict_slashes = False

# Get SECRET_KEY from .env file in parent directory
parent_dir = dirname(dirname(abspath(__file__)))
load_dotenv(os.path.join(parent_dir, '.env'))
app.secret_key = os.getenv('SECRET_KEY')


@app.before_request
def make_session_persistent():
    """
    Make credentials persist after closing the browser, and expire after
    7 days.
    """
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)


def link(text, src=None):
    """
    Create links for alerts.

    @param text: Link text.
    @param src: URL link points to. Set to 'text' if omitted.

    @returns: HTML for link.
    """

    if src is None:
        src = text

    return ('<a href="{0}" class="alert-link">{1}</a>'
            .format(src, text))


settings_msg = ('Make sure you add your Challonge credentials on the '
                '{} page.'.format(link('Settings', '/settings')))


def create_unknown_players_html(unknown_players):
    """Return html of an unordered list to show to the user."""
    # TODO(timkovich): I'd like to put this in the template, but I'm not sure
    # the best way to do this.
    if not unknown_players:
        return ''

    unknown_text = "GAR PR info not found for the following players:<ul>"
    for player in unknown_players:
        unknown_text += ("<li>{name}, seeding {seed}</li>".format(**player))
    unknown_text += "</ul><hr>"

    return unknown_text


def needs_credentials():
    """Checks if Challonge settings have been set."""
    return not all(session.get(key) for key in ['username', 'api_key'])


# Make this function accessible from templates
app.jinja_env.globals.update(needs_credentials=needs_credentials)


def valid_tourney_url(name):
    if not name:
        return False, 'Tournament name is required.'
    elif not re.match(r'[\w:/.]+$', name):
        return False, 'Invalid tournament name.'

    return True, None


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        if needs_credentials():
            flash(settings_msg)

        tourney_url = request.args.get('tourney_url', '')
        shuffle = request.args.get('shuffle', 'on')

        return render_template('index.html',
                               tourney_url=tourney_url,
                               shuffle=shuffle)

    elif request.method == 'POST':
        params = {
            'tourney_url': request.form.get('tourney_url'),
            'shuffle': request.form.get('shuffle', 'off'),
        }

        is_valid_name, err = valid_tourney_url(params['tourney_url'])

        if not is_valid_name:
            flash(err, 'danger')
            return redirect(url_for('main', **params))

        challonge.set_credentials(session['username'], session['api_key'])
        try:
            sorted_players, unknown_players = garpr_seeds_challonge.\
                seed_tournament(params['tourney_url'],
                                region=session['region'],
                                shuffle=params['shuffle'])

        except ValueError as e:
            flash(str(e), 'warning')
            return redirect(url_for('main', **params))
        except garpr_seeds_challonge.NoSuchTournamentError as e:
            flash(str(e), 'warning')
            return redirect(url_for('main', **params))
        except HTTPError as e:
            app.logger.info(e)
            flash('Error accessing Challonge API. Make sure your API key is '
                  'correct.', 'danger')
            return redirect(url_for('main', **params))

        try:
            garpr_seeds_challonge.update_seeds(params['tourney_url'],
                                               sorted_players)
        except HTTPError as e:
            app.logger.info(e)
            flash("Couldn't access {} with the API, are you sure you have "
                  "access to this bracket?".format(params['tourney_url']),
                  'danger')
            return redirect(url_for('main', **params))

        except challonge.api.ChallongeException as e:
            flash(str(e), 'danger')
            return redirect(url_for('main', **params))

        unknown_html = create_unknown_players_html(unknown_players)

        flash(unknown_html + 'Your tournament has been seeded! Check it out '
              '{} to make adjustments. Feel free to run '
              'this again if you add more players.'
              .format(link('here', params['tourney_url'] + '/participants')),
                      'success')
        return redirect(url_for('main', **params))


@app.route('/amateur', methods=['GET', 'POST'])
def amateur():
    if request.method == 'GET':
        if needs_credentials():
            flash(settings_msg)

        default_params = {
            'tourney_url': '',
            'losers_round': 2,
            'elimination': 2,
            'randomize': False,
            'incomplete': False
        }

        params = {}
        for p, default in default_params.items():
            params[p] = request.args.get(p, default)

        return render_template('amateur.html', **params)

    elif request.method == 'POST':
        params = {}
        for p in ['tourney_url', 'losers_round', 'elimination', 'randomize',
                  'incomplete']:
            params[p] = request.form.get(p)

        is_valid_name, err = valid_tourney_url(params['tourney_url'])

        if not is_valid_name:
            flash(err, 'danger')
            return redirect(url_for('amateur', **params))

        challonge.set_credentials(session['username'], session['api_key'])

        try:
            amateur_tourney_url = create_amateur_bracket(
                params['tourney_url'],
                single_elimination=params['elimination'] == 1,
                losers_round_cutoff=int(params['losers_round']),
                randomize_seeds=params['randomize'],
                incomplete=params['incomplete'])

        except AmateurBracketAlreadyExistsError:
            flash('Amateur bracket for this tournament already exists.',
                  'danger')
            return redirect(url_for('amateur', **params))

        except AmateurBracketRequiredMatchesIncompleteError as e:
            flash("The main tournament is not far enough along in the loser's "
                  "bracket to create amateur bracket yet. "
                  "There are <b>{}</b> matches remaining."
                  .format(e.matches_remaining), 'warning')
            return redirect(url_for('amateur', **params))

        except HTTPError as e:
            app.logger.info(e)
            status_code = e.response.status_code

            if status_code == 404:
                flash("Couldn't find tournament: {}"
                      .format(params['tourney_url']), 'danger')
            elif status_code == 401:
                flash('Error accessing Challonge API. Make sure your API key '
                      'is correct.', 'danger')
            else:
                flask('Something went wrong: {} error.'.format(status_code),
                      'danger')
            return redirect(url_for('amateur', **params))

        flash('Your tournament amateur bracket has been created! '
              '{}'.format(link(amateur_tourney_url)), 'success')
        return redirect(url_for('amateur', **params))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        args = {
            'username': session.get('username', ''),
            'api_key': session.get('api_key', ''),
            'region': session.get('region', 'norcal'),
        }

        return render_template('settings.html', **args)

    elif request.method == 'POST':
        for value in ['username', 'api_key', 'region']:
            session[value] = request.form.get(value)

        flash('Credentials saved!', 'success')
        return redirect(url_for('settings'))


@app.route('/logout')
def logout():
    session.clear()

    flash('You are logged out.')
    return redirect('settings')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')
