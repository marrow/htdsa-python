# encoding: utf-8

from __future__ import unicode_literals

if __debug__:
	import time

from datetime import datetime, timedelta
from requests import codes
from requests.auth import AuthBase

# Protocol-Mandated Imports
from binascii import hexlify, unhexlify
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey
from ecdsa.keys import BadSignatureError


log = __import__('logging').getLogger(__name__)


try:
	unicode = unicode
	str = str
except:
	unicode = str
	str = bytes


class SignedAuth(AuthBase):
	CANONICAL_REQUEST_STRUCTURE = "{r.method}\n{r.headers[date]}\n{r.url}\n{r.body}"  # Ref: Application 2.i.
	CANONICAL_RESPONSE_STRUCTURE = "{identity}\n{r.request.method}\n{date}\n" \
			"{r.request.url}\n{r.text}"  # Ref: Server 4.ii.
	
	def __init__(self, identity, private, public):
		"""Configure HTDSA signed request/response authentication.
		
		To perform the cryptographic operations required for the HTDSA protocol you must pass in either instances of
		`ecdsa` signing and verifying keys, or their hex-encoded versions which will be converted automatically.
		
		Additionally, the identity token (opaque identifier) assigned to your client application by the provider will
		need to be passed in so we can identify ourselves.
		
		The private key is your application's private key. The public key is the provider's service key you were given
		when registering your application.
		"""
		
		self.identity = identity
		self.private = SigningKey.from_string(unhexlify(private)) if isinstance(private, (str, unicode)) else private
		self.public = VerifyingKey.from_string(unhexlify(public)) if isinstance(public, (str, unicode)) else public
	
	def __call__(self, request):
		if __debug__:
			log.debug("Signing HTTP {method} request.".format(method=request.method),
					extra=dict(request=id(request), method=request.method, url=request.url))
			start = time.time()
		
		request.headers['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')  # Ref: Application 2.i.b.
		request.headers['X-Service'] = self.identity  # Ref: Application 2.ii.a.
		
		if request.body is None:  # We need at least an empty string to avoid errors later.
			request.body = ''
		
		canon = self.CANONICAL_REQUEST_STRUCTURE.format(method=request.method, r=request).encode('utf-8')
		
		request.headers['X-Signature'] = hexlify(self.private.sign(canon))  # Ref: Application 2.ii.b.
		
		if __debug__:
			duration = time.time() - start
			log.debug("Signing of HTTP {method} request took {time} seconds.".format(
					method = request.method,
					time = duration
				), extra = dict(request=id(request), method=request.method, url=request.url, duration=duration))
		
		request.register_hook('response', self.validate)
		
		return request
	
	def validate(self, response, *args, **kw):
		if response.status_code != codes.ok:
			if __debug__:
				log.debug("Skipping validation of non-200 response.")
			return
		
		if 'X-Signature' not in response.headers:
			raise BadSignatureError("No signature present in resopnse to signed request.")
		
		if __debug__:
			log.debug("Validating response signature.", extra=dict(
					request = id(response.request),
					method = response.request.method,
					url = response.request.url,
					signature = response.headers['X-Signature'],
				))
		
		canon = self.CANONICAL_RESPONSE_STRUCTURE.format(identity=self.identity, r=response, date=response.headers['Date'])
		date = datetime.strptime(response.headers['Date'], '%a, %d %b %Y %H:%M:%S GMT')
		
		if datetime.utcnow() - date > timedelta(seconds=30):  # Ref: Application 2.i.b.
			log.warning("Rejecting stale response.", extra=dict(
				request=id(response.request), method=response.request.method, url=response.request.url))
			
			raise BadSignatureError("Rejecting stale response.")
		
		# We allow responses 1s from the future to account for slight clock skew.
		if datetime.utcnow() - date < timedelta(seconds=-1):
			log.warning("Received a request from the future; please check system time NTP synchronization.")
			raise BadSignatureError("Rejecting message from the future.")  # Einstein says, "No."
		
		# Raises an exception on failure.
		try:
			self.public.verify(
					unhexlify(response.headers['X-Signature'].encode('utf-8')),
					canon.encode('utf-8'),
					hashfunc=sha256
				)
		
		except BadSignatureError:
			# Try verifying again with the time adjusted by one second.
			date = (date - timedelta(seconds=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
			canon = self.CANONICAL_RESPONSE_STRUCTURE.format(identity=self.identity, r=response, date=date)
			self.public.verify(
					unhexlify(response.headers['X-Signature'].encode('utf-8')),
					canon.encode('utf-8'),
					hashfunc=sha256
				)

