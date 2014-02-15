from django.contrib.auth import get_user_model
import ldap, ldap.filter

User = get_user_model()

class UChicagoLDAPBackend(object):
	LDAP_SERVER = "ldaps://ldap.uchicago.edu:636"

	def __init__(self):
		self.conn = ldap.initialize(self.LDAP_SERVER)
		self._udCache = {}

	def bind(self, cnetid, password):
		cnetid = ldap.filter.escape_filter_chars(cnetid)
		try:
			self.conn.simple_bind_s("uid=%s,ou=people,dc=uchicago,dc=edu" % cnetid, password)
		except:
			return False
		return True

	def get_user_data(self, cnetid): # look up a user by CNetID
		if cnetid in self._udCache:
			return self._udCache[cnetid]
		cnetid = ldap.filter.escape_filter_chars(cnetid)
		query = "(&(uid=%s)(objectclass=inetOrgPerson))" % (cnetid)
		results = self.conn.search_ext_s("dc=uchicago,dc=edu", ldap.SCOPE_SUBTREE, query)
		if results:
			user_data = results[0][1]
			self._udCache[user_data['uid'][0]] = user_data
			return user_data
		else:
			return None

	def provision_user(self, user_data):
		try:
			return (User.objects.get(username=user_data['uid'][0]), False)
		except User.DoesNotExist:
			user = User.objects.create_user(username=user_data['uid'][0], email=user_data['mail'][0], first_name=user_data['givenName'][0], last_name=user_data['sn'][0])
			return (user, True)

	def authenticate(self, username=None, password=None):
		if username and password:
			cnetid = ldap.filter.escape_filter_chars(username)
			bound = self.bind(cnetid, password)
			if bound:
				user_data = self.get_user_data(cnetid)
				try:
					user = User.objects.get(username=cnetid)
					if user_data: # update info
						user.username = user_data['uid'][0]
						user.email = user_data['mail'][0]
						if user_data.get('givenName'):
							user.first_name = user_data['givenName'][0]
						else:
							user.first_name = 'Unknown'
						if user_data.get('sn'):
							user.last_name = user_data['sn'][0]
						else:
							user.last_name = 'Unknown'
						user.save()
					return user
				except User.DoesNotExist:
					if user_data:
						return self.provision_user(user_data)[0]
		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None

	def get_user_major(self, cnetid):
		user_data = self.get_user_data(cnetid)
		if user_data:
			ou = user_data.get('ou')
			if ou:
				for v in ou:
					if v.find('College:') == 0:
						return v
				return ou[0]
		return 'N/A'
