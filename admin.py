import settings
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from views import AdminPage

application = webapp.WSGIApplication([('.*', AdminPage)], debug=settings.DEBUG)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
