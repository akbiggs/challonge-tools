#!/usr/bin/env python
"""
This is a webapp written in Flask to access the Challonge tools backend,
and make it easier for the average user to use.

"""
import challonge
from datetime import timedelta
from flask import Flask, render_template, redirect, request, flash, session,\
        url_for
import re
from requests.exceptions import HTTPError

from create_amateur_bracket import create_amateur_bracket,\
        MainTournamentNotFarEnoughAlong, AmateurBracketAlreadyExists
import garpr_seeds_challonge


app = Flask(__name__)
# TODO: not this
app.secret_key = "Every Who Down in Whoville Liked Christmas a lot...  But the Grinch,Who lived just north of Whoville, Did NOT!  The Grinch hated Christmas! The whole Christmas season!  Now, please don't ask why. No one quite knows the reason.  It could be his head wasn't screwed on just right.  It could be, perhaps, that his shoes were too tight."
app.url_map.strict_slashes = False


@app.before_request
def make_session_persistent():
    """
    Make credentials persist after closing the browser, and expire after
    7 days.
    """
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)


settings_msg = ('Make sure you add your Challonge credentials on the '
                '<a href="settings">Settings</a> page.')


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
        # TODO: Form and session error checking
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
        except HTTPError:
            flash('Error accessing Challonge API. Make sure your API key is '
                  'correct.', 'danger')
            return redirect(url_for('main', **params))

        tourney_url = "http://challonge.com/{0}".format(params['tourney_name'])

        try:
            garpr_seeds_challonge.update_seeds(params['tourney_name'],
                                               sorted_players)
        except HTTPError:
            flash("Couldn't access {} with the API, are you sure you have "
                  "access to this bracket?".format(tourney_url), 'warning')
            return redirect(url_for('main', **params))

        flash('Your tournament has been seeded! Check it out '
              '<a href="{0}">here</a> to make adjustments. Feel free to run '
              'this again if you add more players.'
              .format(tourney_url + '/participants'))
        return redirect(url_for('main', **params))


@app.route('/amateur', methods=['GET', 'POST'])
def amateur():
    if request.method == 'GET':
        if needs_credentials():
            flash(settings_msg)

        params = {}
        for p, default in [('tourney_name', ''),
                           ('losers_round', 2),
                           ('elimination', 2),
                           ('randomize', False)]:
            params[p] = request.args.get(p, default)

        app.logger.info(params)

        return render_template('amateur.html', **params)

    elif request.method == 'POST':
        params = {}
        for p in ['tourney_name', 'losers_round', 'elimination', 'randomize']:
            value = request.form.get(p)

            if p in {'losers_round', 'elimination'}:
                value = int(value)

            params[p] = value

        is_valid_name, err = valid_tourney_name(params['tourney_name'])

        # TODO: amateur page takes GET params
        if not is_valid_name:
            flash(err, 'danger')
            return redirect(url_for('amateur', **params))

        # if any(p is None for p in params):
        #     # TODO: error checking
        #     pass

        challonge.set_credentials(session['username'], session['api_key'])

        try:
            amateur_tourney_url = create_amateur_bracket(
                params['tourney_name'],
                single_elimination=params['elimination'] == 1,
                losers_round_cutoff=params['losers_round'],
                randomize_seeds=params['randomize'])

        except AmateurBracketAlreadyExists:
            flash('Amateur bracket for this tournament already exists.',
                  'danger')
            return redirect(url_for('amateur', **params))

        except MainTournamentNotFarEnoughAlong:
            flash("Main tournament is not far enough along in the loser's "
                  "bracket to create amateur bracket yet.", 'warning')
            return redirect(url_for('amateur', **params))

        flash('Your tournament amateur bracket has been created! '
              '<a href="{0}">{0}</a>'.format(amateur_tourney_url))
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

        flash('Credentials saved!')
        return redirect(url_for('settings'))


@app.route('/logout')
def logout():
    session.clear()

    flash('You are logged out.')
    return redirect('settings')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
