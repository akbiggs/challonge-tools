from flask import Flask, render_template, redirect, request, flash, session

app = Flask(__name__)
# TODO: not this
app.secret_key = "Every Who Down in Whoville Liked Christmas a lot...  But the Grinch,Who lived just north of Whoville, Did NOT!  The Grinch hated Christmas! The whole Christmas season!  Now, please don't ask why. No one quite knows the reason.  It could be his head wasn't screwed on just right.  It could be, perhaps, that his shoes were too tight."
app.url_map.strict_slashes = False


settings_msg = ('Make sure you add your Challonge credentials on the '
                '<a href="settings">Settings</a> page.')

def needs_credentials():
    """Checks if Challonge settings have been set."""
    return not all(key in session for key in ['username', 'api_key'])

app.jinja_env.globals.update(needs_credentials=needs_credentials)


@app.route('/')
def main():
    if needs_credentials():
        flash(settings_msg)

    return render_template('index.html',
                           shuffle=True)


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


@app.route('/amateur')
def amateur():
    if needs_credentials():
        flash(settings_msg)

    return render_template('amateur.html',
                           losers_round=2,
                           elimination=2,
                           randomize=False)


@app.route('/logout')
def logout():
    session.clear()

    flash('You are logged out.')
    return redirect('settings')

