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

from create_amateur_bracket import create_amateur_bracket,\
        MainTournamentNotFarEnoughAlong, AmateurBracketAlreadyExists
import garpr_seeds_challonge


app = Flask(__name__)
sslify = SSLify(app)
app.url_map.strict_slashes = False

# Get SECRET_KEY from env variable
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
    """Create links for alerts."""
    if src is None:
        src = text

    return ('<a href="{0}" class="alert-link">{1}</a>'
        .format(src, text))


settings_msg = ('Make sure you add your Challonge credentials on the '
                '{} page.'.format(link('Settings', '/settings')))


def needs_credentials():
    """Checks if Challonge settings have been set."""
    return not all(key in session for key in ['username', 'api_key'])


# Make this function accessible from templates
app.jinja_env.globals.update(needs_credentials=needs_credentials)


def valid_tourney_name(name):
    if not name:
        return False, 'Tournament name is required.'
    elif not re.match('\w+$', name):
        return False, 'Invalid tournament name.'

    return True, ''

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        if needs_credentials():
            flash(settings_msg)

        tourney_name = request.args.get('tourney_name', '')
        shuffle = request.args.get('shuffle', 'on')

        return render_template('index.html',
                               tourney_name=tourney_name,
                               shuffle=shuffle)

    elif request.method == 'POST':
        params = {
            'tourney_name': request.form.get('tourney_name'),
            'shuffle': request.form.get('shuffle', 'off'),
        }

        is_valid_name, err = valid_tourney_name(params['tourney_name'])

        if not is_valid_name:
            flash(err, 'danger')
            return redirect(url_for('main', **params))

        challonge.set_credentials(session['username'], session['api_key'])
        try:
            # TODO: Get the status messages about which players weren't
            # found on garpr
            sorted_players = garpr_seeds_challonge.seed_tournament(
                                 params['tourney_name'],
                                 region=session['region'],
                                 shuffle=params['shuffle'])
        except garpr_seeds_challonge.NoSuchTournamentError as e:
            flash(str(e), 'warning')
            return redirect(url_for('main', **params))
        except HTTPError as e:
            app.logger.info(e)
            flash('Error accessing Challonge API. Make sure your API key is '
                  'correct.', 'danger')
            return redirect(url_for('main', **params))

        tourney_url = "http://challonge.com/{0}".format(params['tourney_name'])

        try:
            garpr_seeds_challonge.update_seeds(params['tourney_name'],
                                               sorted_players)
        except HTTPError:
            flash("Couldn't access {} with the API, are you sure you have "
                  "access to this bracket?".format(tourney_url), 'danger')
            return redirect(url_for('main', **params))

        flash('Your tournament has been seeded! Check it out '
              '{} to make adjustments. Feel free to run '
              'this again if you add more players.'
              .format(link('here', tourney_url + '/participants')), 'success')
        return redirect(url_for('main', **params))


@app.route('/amateur', methods=['GET', 'POST'])
def amateur():
    if request.method == 'GET':
        if needs_credentials():
            flash(settings_msg)

        default_params = {
            'tourney_name': '',
            'losers_round': 2,
            'elimination': 2,
            'randomize': False
        }

        params = {}
        for p, default in default_params.items():
            params[p] = request.args.get(p, default)

        return render_template('amateur.html', **params)

    elif request.method == 'POST':
        params = {}
        for p in ['tourney_name', 'losers_round', 'elimination', 'randomize']:
            params[p] = request.form.get(p)

        is_valid_name, err = valid_tourney_name(params['tourney_name'])

        if not is_valid_name:
            flash(err, 'danger')
            return redirect(url_for('amateur', **params))

        challonge.set_credentials(session['username'], session['api_key'])

        try:
            amateur_tourney_url = create_amateur_bracket(
                params['tourney_name'],
                single_elimination=params['elimination'] == 1,
                losers_round_cutoff=int(params['losers_round']),
                randomize_seeds=params['randomize'])

        except AmateurBracketAlreadyExists:
            flash('Amateur bracket for this tournament already exists.',
                  'danger')
            return redirect(url_for('amateur', **params))

        except MainTournamentNotFarEnoughAlong as e:
            flash("The main tournament is not far enough along in the loser's "
                  "bracket to create amateur bracket yet. "
                  "There are {} matches remaining."
                  .format(e.matches_remaining), 'warning')
            return redirect(url_for('amateur', **params))

        except HTTPError as e:
            app.logger.info(e)
            status_code = e.response.status_code

            if status_code == 404:
                flash("Couldn't find tournament: {}"
                      .format(params['tourney_name']), 'danger')
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
