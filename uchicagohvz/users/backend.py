from django.contrib.auth import get_user_model
import ldap, ldap.filter

User = get_user_model()

class UChicagoLDAPBackend(object):
	LDAP_SERVER = "ldaps://ldap.uchicago.edu:636"

	def authenticate(self, username=None, password=None):
		if username and password:
			cnetid = ldap.filter.escape_filter_chars(username)
			conn = ldap.initialize(self.LDAP_SERVER)
			try:
				conn.simple_bind_s("uid=%s,ou=people,dc=uchicago,dc=edu" % cnetid, password)
			except ldap.INVALID_CREDENTIALS:
				return None
			query = "(&(uid=%s)(objectclass=inetOrgPerson))" % (cnetid)
			results = conn.search_ext_s("dc=uchicago,dc=edu", ldap.SCOPE_SUBTREE, query)
			if results:
				user_data = results[0][1]
			else:
				user_data = None
			try:
				user = User.objects.get(username=cnetid)
				if user_data:
					user.username = user_data['uid'][0]
					user.email = user_data['mail'][0]
					user.first_name = user_data['givenName'][0]
					user.last_name = user_data['sn'][0]
					user.save()
				return user
			except User.DoesNotExist:
				if user_data:
					user = User.objects.create_user(username=user_data['uid'][0], email=user_data['mail'][0], first_name=user_data['givenName'][0], last_name=user_data['sn'][0])
					return user
		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None

	@staticmethod
	def get_user_major(username):
		cnetid = ldap.filter.escape_filter_chars(username)
		conn = ldap.initialize(UChicagoLDAPBackend.LDAP_SERVER)
		query = "(&(uid=%s)(objectclass=inetOrgPerson))" % (cnetid)
		results = conn.search_ext_s("dc=uchicago,dc=edu", ldap.SCOPE_SUBTREE, query)
		if results:
			user_data = results[0][1]
			ou = user_data["ou"]
			if ou:
				for v in ou:
					if v.find("College:") == 0:
						return v
				return ou[0]
		return "N/A"