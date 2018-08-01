"""
This is a webapp written in Flask to access the Challonge tools backend,
and make it easier for the average user to use.

"""
import challonge
from datetime import timedelta
from flask import Flask, render_template, redirect, request, flash, session
from requests.exceptions import HTTPError

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


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        if needs_credentials():
            flash(settings_msg)

        return render_template('index.html',
                               shuffle=True)

    elif request.method == 'POST':
        # TODO: Form and session error checking
        tourney_name = request.form.get('tourney_name')
        shuffle = request.form.get('shuffle')
        challonge.set_credentials(session['username'], session['api_key'])
        sorted_players = garpr_seeds_challonge.seed_tournament(
                             tourney_name,
                             region=session['region'],
                             shuffle=shuffle)

        tourney_url = "http://challonge.com/{0}".format(tourney_name)

        try:
            garpr_seeds_challonge.update_seeds(tourney_name, sorted_players)
        except HTTPError:
            flash("Couldn't access {} with the API, are you sure you have "
                  "access to this bracket?".format(tourney_url), 'danger')
            return redirect('/')

        flash('Your tournament has been created at <a href="{0}">{0}</a>'
              .format(tourney_url))
        return redirect('/')


@app.route('/amateur')
def amateur():
    if needs_credentials():
        flash(settings_msg)

    return render_template('amateur.html',
                           losers_round=2,
                           elimination=2,
                           randomize=False)


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
        return redirect('settings')


@app.route('/logout')
def logout():
    session.clear()

    flash('You are logged out.')
    return redirect('settings')

