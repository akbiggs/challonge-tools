from gaesessions import get_current_session
import jinja2
import logging
import os
import webapp2


class Page(webapp2.RequestHandler):
    """This class contains helper functions for our pages."""
    def render_template(self, html, **values):
        JINJA_ENVIRONMENT = jinja2.Environment(
                loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                extensions=['jinja2.ext.autoescape'],
                autoescape=True)

        template = JINJA_ENVIRONMENT.get_template(html)
        self.response.write(template.render(values))

    def redirect_with_msg(self, dst, msg):
        get_current_session()['msg'] = msg
        self.redirect(dst)

    def has_credentials(self, session):
        """Checks if Challonge settings have been set."""
        return session.get('username') and session.get('api_key')


class MainPage(Page):
    def get(self):
        session = get_current_session()

        self.render_template('index.html',
                             title='Seed Tournament',
                             has_credentials=self.has_credentials(session),
                             shuffle=True)


class SettingsPage(Page):
    def get(self):
        session = get_current_session()
        args = {
            'username': session.get('username', ''),
            'api_key': session.get('api_key', ''),
            'region': session.get('region', 'norcal'),
            # Get the msg then remove it
            'msg': session.pop('msg'),
        }
        self.render_template('settings.html',
                             title='Settings',
                             **args)

    def post(self):
        session = get_current_session()

        for value in ['username', 'api_key', 'region']:
            session[value] = self.request.get(value)

        self.redirect_with_msg('settings', 'Credentials saved!')


class AmateurPage(Page):
    def get(self):
        session = get_current_session()

        self.render_template('amateur.html',
                             title='Create Amateur Bracket',
                             has_credentials=self.has_credentials(session),
                             losers_round=2,
                             elimination=2,
                             randomize=False)


class LogoutPage(Page):
    def get(self):
        session = get_current_session()
        session.terminate()

        self.redirect_with_msg('settings', 'You have been logged out.')


app = webapp2.WSGIApplication([
        ('/', MainPage),
        ('/amateur', AmateurPage),
        ('/settings', SettingsPage),
        ('/logout', LogoutPage),
], debug=True)
