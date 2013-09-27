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
			try:
				user = User.objects.get(username=cnetid)
				return user
			except User.DoesNotExist:
				query = "(&(uid=%s)(objectclass=inetOrgPerson))" % (cnetid)
				result = conn.search_ext_s("dc=uchicago,dc=edu", ldap.SCOPE_SUBTREE, query)
				print result
				if result:
					user_data = result[0][1]
					user = User.objects.create_user(username=user_data['uid'][0], email=user_data['mail'][0], first_name=user_data['givenName'][0], last_name=user_data['sn'][0])
					return user
		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None