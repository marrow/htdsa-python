# encoding: utf-8

"""An extremely simple (yet powerful) generic REST interface utilizing HTDSA signing."""

from __future__ import unicode_literals

import requests


log = __import__('logging').getLogger(__name__)


try:
	unicode = unicode
	str = str
except:
	unicode = str
	str = bytes


from .auth import SignedAuth


class API(object):
	"""An API endpoint proxy object and factory for other API endpoints.
	
	Attributes (other than the methods defined at the class level) and array subscripts result in a new API instance
	with the requested attribute (or subscript) appended as a path element. Additionally, positional arguments are
	appended as path elements to the API endpoint URL. Keyword arguments, on applicable HTTP methods, are passed
	through as Requests' `data` argument. (Currently; the option to use JSON request bodies will come in a future
	revision.)
	
	All of the above results in an API making requests like:
	
	* `api.sso.grant.get()` -> `.../sso/grant`
	* `api.account['amcgregor'].get()` -> `.../account/amcgregor`
	* `api.company.get('Google')` -> `.../company/Google`
	"""
	
	__slots__ = ('endpoint', 'identity', 'private', 'public', 'pool', 'options', 'json')
	
	def __init__(self, endpoint, identity, private, public, options=None, json=None, pool=None):
		"""Construct a new API endpoint base.
		
		The base `endpoint` must be defined as an absolute URL. The `identity`, `private`, and `public` arguments are
		passed through to the underlying `SignedAuth` instance. The optional `options` argument defines additional
		keyword arguments (as a dictionary or other mapping) to pass to the underlying `requests.request` call. The
		optional `json` argument defines additional keyword arguments to pass through to the `result.json` call. You
		can additionally pass a prepared `requests.Session` request `pool`.
		"""
		
		self.endpoint = unicode(endpoint).rstrip('/')
		self.options = options if options else dict()
		self.options.setdefault('allow_redirects', False)
		self.json = json if json else dict()
		
		if 'auth' not in self.options:
			self.options['auth'] = SignedAuth(identity, private, public)
		
		if not pool:
			self.pool = requests.Session()
		else:
			self.pool = pool
	
	def __getattr__(self, name):
		return API(self.endpoint + '/' + unicode(name), None, None, None, self.options, self.pool)
	
	__getitem__ = __getattr__  # Allow for use of reserved words as endpoints, as well as non-symbol named endpoints.
	
	def _uri(self, args=None):
		uri = self.endpoint
		
		if args:
			uri += '/' + '/'.join(unicode(arg) for arg in args)
		
		return uri
	
	def _request(self, method, args, kwargs, params=None, json=True):
		result = self.pool.request(method, self._uri(args), params=params, data=kwargs, **self.options)
		
		if not result.status_code == requests.codes.ok:
			return None
		
		return result.json(**self.json) if json else result
	
	@property
	def _allowed(self):
		result = self.pool.request('OPTIONS', self._uri(), **self.options)
		
		if not result.status_code == requests.codes.ok:
			return None
		
		return (i.strip() for i in result.headers['Allow'].split(','))
	
	def get(self, *args, **kwargs):
		return self._request('GET', args, None, kwargs)
	
	def head(self, *args, **kwargs):
		return self._request('HEAD', args, None, kwargs, False)
	
	def post(self, *args, **kwargs):
		return self._request('POST', args, kwargs)
	
	def put(self, *args, **kwargs):
		return self._request('POST', args, kwargs)
	
	def delete(self, *args, **kwargs):
		return self._request('DELETE', args, None, kwargs)
	
	def patch(self, *args, **kwargs):
		return self._request('PATCH', args, kwargs)

