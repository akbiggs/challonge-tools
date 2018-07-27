from gaesessions import SessionMiddleware
import os

def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app,
                            # TODO: don't do this
                            cookie_key="Every Who Down in Whoville Liked Christmas a lot... But the Grinch,Who lived just north of Whoville, Did NOT! The Grinch hated Christmas! The whole Christmas season! Now, please don't ask why. No one quite knows the reason.",
                            no_datastore=True)
    return app
