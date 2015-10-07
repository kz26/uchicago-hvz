from django.contrib.auth.models import User
import ldap, ldap.filter


class UChicagoLDAPBackend(object):
	LDAP_SERVER = "ldaps://ldap.uchicago.edu:636"

	def __init__(self):
		self.conn = ldap.initialize(self.LDAP_SERVER)

	def bind(self, cnetid, password):
		cnetid = ldap.filter.escape_filter_chars(cnetid)
		try:
			self.conn.simple_bind_s("uid=%s,ou=people,dc=uchicago,dc=edu" % cnetid, password)
		except ldap.LDAPError:
			return False
		return True

	def get_user_data(self, cnetid): # look up a user by CNetID
		cnetid = ldap.filter.escape_filter_chars(cnetid)
		query = "(&(uid=%s)(objectclass=inetOrgPerson))" % (cnetid)
		results = self.conn.search_ext_s("dc=uchicago,dc=edu", ldap.SCOPE_SUBTREE, query)
		if results:
			user_data = results[0][1]
			if not user_data.get('uid'):
				return None
			if not user_data.get('givenName'):
				user_data['givenName'] = ['Unknown']
			if not user_data.get('sn'):
				user_data['sn'] = ['Unknown']
			if not user_data.get('mail'):
				user_data['mail'] = ["%s@uchicago.edu" % (cnetid)]
			return user_data
		else:
			return None

	def provision_user(self, user_data, password=None):
		try:
			return (User.objects.get(username=user_data['uid'][0]), False)
		except User.DoesNotExist:
			user = User.objects.create_user(username=user_data['uid'][0], password=password,
				email=user_data['mail'][0], first_name=user_data['givenName'][0], last_name=user_data['sn'][0]
			)
			return (user, True)

	def authenticate(self, username=None, password=None):
		if username and password:
			cnetid = ldap.filter.escape_filter_chars(username).lower()
			bound = self.bind(cnetid, password)
			if bound:
				user_data = self.get_user_data(cnetid)
				if user_data:
					try:
						user = User.objects.get(username__iexact=cnetid)
					except User.DoesNotExist:
						user = self.provision_user(user_data, password)[0]
					else:
						user.set_password(password)
					if user.profile.use_ldap_name:
						user.first_name = user_data['givenName'][0]
						user.last_name = user_data['sn'][0]
					user.email = user_data['mail'][0]
					user.save()
					return user
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
