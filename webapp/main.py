from gaesessions import get_current_session
import jinja2
import logging
import os
import webapp2


class Page(webapp2.RequestHandler):
    def template_render(self, html, **values):
        JINJA_ENVIRONMENT = jinja2.Environment(
                loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                extensions=['jinja2.ext.autoescape'],
                autoescape=True)

        values['title'] = self.title
        template = JINJA_ENVIRONMENT.get_template(html)
        self.response.write(template.render(values))

    def redirect_with_msg(self, dst, msg):
        get_current_session()['msg'] = msg
        self.redirect(dst)


    def session_to_args(self):
        session = get_current_session()

        return {
            'username': session.get('username', ''),
            'api_key': session.get('api_key', ''),
            'region': session.get('region', 'norcal'),
            # Get the msg then remove it
            'msg': session.pop('msg'),
        }


    def check_for_incomplete_settings(self, session):
        if not session.get('username') or not session.get('api_key'):
            session['msg'] = ('Make sure you add your Challonge credentials '
                              'on the "Settings" page')


class MainPage(Page):
    def __init__(self, request, response):
        super(MainPage, self).__init__(request, response)
        self.title = 'Seed Tournament'

    def get(self):
        session = get_current_session()
        self.check_for_incomplete_settings(session)

        self.template_render('index.html',
                             shuffle=True,
                             msg=session.pop('msg'))


class SettingsPage(Page):
    def __init__(self, request, response):
        super(SettingsPage, self).__init__(request, response)
        self.title = 'Settings'

    def get(self):
        self.template_render('settings.html', **self.session_to_args())

    def post(self):
        session = get_current_session()

        for value in ['username', 'api_key', 'region']:
            session[value] = self.request.get(value)

        session['msg'] = 'Credentials saved!'

        self.template_render('settings.html', **self.session_to_args())


class AmateurPage(Page):
    def __init__(self, request, response):
        super(AmateurPage, self).__init__(request, response)
        self.title = 'Create Amateur Bracket'

    def get(self):
        session = get_current_session()
        self.check_for_incomplete_settings(session)

        self.template_render('amateur.html',
                             msg=session.pop('msg'),
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
