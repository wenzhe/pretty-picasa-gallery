import os, logging, urllib

from xml.dom import minidom
from random import choice, shuffle

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


from models import UserPrefs
import settings

class BasePage(webapp.RequestHandler):
	"""Base class to handle requests."""
	
	gphoto_namespace = 'http://schemas.google.com/photos/2007'
	media_namespace = 'http://search.yahoo.com/mrss/'
	template_values = {}
	userprefs = None
	


class AdminPage(BasePage):
	"""Class to handle requests to the admin directory."""


	def RenderAdminPage(self):
		"""Renders the admin page"""
		logging.info('RenderAdminPage called')
		
		self.template_values['title'] = self.userprefs.site_title+" gallery admin"
		self.template_values['album_name'] = "admin"
		self.template_values['logout_url'] = users.create_logout_url('/')
		if users.get_current_user() != self.userprefs.user:
			self.template_values['current_user'] = users.get_current_user()
		self.template_values['user'] = self.userprefs
		self.template_values['settings'] = settings
		self.template_values['debug'] = settings.DEBUG
		
		backend = self.userprefs.GetPhotoBackend()
		
		try:
			albums = backend.GetAllAlbums()
		except:
			albums = []
		album_list = []
		featured_albums = self.userprefs.featured_albums
		for a in albums:
			if a['title'] in featured_albums:
				a['featured'] = True
			else:
				a['featured'] = False
			album_list.append(a)
		album_list.append({'id': 'all', 'title': 'all', 'featured': ('all' in featured_albums)})
		
		self.template_values['all_albums'] = album_list
		path = os.path.join(os.path.dirname(__file__), 'admin.html')
		self.response.out.write(template.render(path, self.template_values))

	def InitializeUser(self):
		# Get the owner of the app
		self.userprefs = UserPrefs.all().get()

		if not self.userprefs:
			# Create the owner of the app
			self.userprefs = UserPrefs(user=users.get_current_user())
			self.userprefs.put()

	def get(self):
		"""Default method called upon entry to the app."""

		self.InitializeUser()

		# Reset template values with every new request.
		self.template_values = {
		}

		self.RenderAdminPage()
	
	def post(self):
		"""Save the admin settings."""
		
		self.InitializeUser()
		
		self.template_values = {
		}
		
		# Get the admin settings and save them
		try:
			if self.request.get('clear-cache'):
				backend = self.userprefs.GetPhotoBackend()
				
				backend.ClearCache()
				
				self.template_values['cache_cleared'] = True
			else:
				self.userprefs.photo_backend = int(self.request.get('backend'))
				self.userprefs.SetUsername(self.request.get('backend-id'))
				
				self.userprefs.site_title = self.request.get('site-title').strip()
				self.userprefs.site_header = self.request.get('site-header').strip()
				
				self.userprefs.thumb_size = int(self.request.get('thumb-size'))
				if self.userprefs.photo_backend == settings.PHOTO_BACKEND_FLICKR:
					self.userprefs.thumb_size = 75
				elif self.userprefs.photo_backend == settings.PHOTO_BACKEND_PICASA and self.userprefs.thumb_size == 75:
					self.userprefs.thumb_size = 72
				self.userprefs.thumb_cropped = bool(self.request.get('thumb-cropped'))
				self.userprefs.full_size = int(self.request.get('full-size'))
				self.userprefs.homepage_size = int(self.request.get('homepage-size'))
				
				backend = self.userprefs.GetPhotoBackend()
				
				homepage_album = self.request.get('homepage-album').strip()
				for album in backend.GetAllAlbums():
					if album['title'] == homepage_album:
						self.userprefs.homepage_album = homepage_album
				
				featured_albums = self.request.get('featured-album', allow_multiple=True)
				
				self.userprefs.featured_albums = featured_albums
				
				self.userprefs.merchant_id = self.request.get('merchant-id')
				self.userprefs.analytics_id = self.request.get('analytics-id')
				
				self.userprefs.put()
				
				self.template_values['saved'] = True
		except (TypeError, ValueError), e:
			self.template_values['error'] = True
			self.template_values['error_message'] = str(e)
		
		
		self.RenderAdminPage()


class MainPage(BasePage):
	"""Class to handle requests to the root directory."""

	def GetSinglePhoto(self, album_name, photo_id):
		"""Retrieves URL for a specific photo.

		Args:
			album_name: string name of Picasa web album.
			photo_id: integer photo ID.

		Returns:
			String URL pointing to the large photo.
		"""

		logging.info('GetSinglePhoto with '+album_name+' and '+photo_id)

		# Attempt to retrieve url from memcache, keyed on album_name + photo_id.
		photo_url = memcache.get(album_name + '_' + photo_id)
		if settings.MEMCACHE_ENABLED and photo_url is not None:
			logging.info('GetSinglePhoto memcache hit')
			return photo_url

		url = '%s/album/%s/photoid/%s?imgmax=800' % (self.GetApiUrl(), album_name, photo_id)
		logging.info('GetSinglePhoto url '+url)
		result = urlfetch.fetch(url)
		try:
			dom = minidom.parseString(result.content)
			for node in dom.getElementsByTagNameNS(self.media_namespace, 'content'):
				memcache.add(album_name + '_' + photo_id, node.getAttribute('url'),
						settings.MEMCACHE_PHOTO_EXPIRATION)
				logging.info('GetSinglePhoto photo url '+node.getAttribute('url'))
				return node.getAttribute('url')
		except:
			logging.info('GetSinglePhoto exception')
			return None


	def RenderAlbum(self, album_name):
		"""Renders an HTML page for a specific album.

		Args:
			album_name: string name of Picasa album.
		"""
		backend = self.userprefs.GetPhotoBackend()
		
		logging.info('RenderAlbum called')
		self.template_values['album_name'] = album_name
		self.template_values['photos'] = backend.GetPhotosInAlbum(album_name, featured=self.userprefs.featured_albums)
		
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, self.template_values))

	def RenderHomepage(self):
		"""Renders homepage with a single big photo"""
		logging.info('RenderHomepage called')
		
		try:
			backend = self.userprefs.GetPhotoBackend()
			backend.imgmax = self.userprefs.homepage_size
			photos = backend.GetPhotosInAlbum(self.userprefs.homepage_album)
			shuffle(photos)
			for photo in photos:
				if photo['width'] > photo['height']:
					break
			
			self.template_values['homepage_photo'] = {
				'id': photo['id'],
				'album': self.userprefs.homepage_album,
				'src': photo['url'],
			}
		except Exception, e:
			logging.info("Got an error: %s" % str(e))
		path = os.path.join(os.path.dirname(__file__), 'index.html')
		self.response.out.write(template.render(path, self.template_values))

	def get(self, album_name=None):
		"""Default method called upon entry to the app."""
		# Get the owner of the app
		if not self.userprefs:
			self.userprefs = UserPrefs.all().get()

		if not self.userprefs:
			# Redirect to the admin page
			self.redirect('/admin/')
			return
		
		backend = self.userprefs.GetPhotoBackend()
		
		# Reset template values with every new request.
		self.template_values = {
		        'user': self.userprefs,
			'title': self.userprefs.site_title+" gallery",
			'albums': backend.GetFeaturedAlbums(self.userprefs.featured_albums),
			'debug': settings.DEBUG,
		}
		if users.is_current_user_admin():
			self.template_values['logout_url'] = users.create_logout_url('/')

		#album_name = self.request.get('album_name')
		if album_name:
			self.RenderAlbum(album_name)
		else:
			self.RenderHomepage()
