from django.contrib.auth import get_user_model
import ldap

User = get_user_model()

class UChicagoLDAPBackend(object):
	LDAP_SERVER = "ldaps://ldap.uchicago.edu:636"

	def authenticate(self, cnetid=None, password=None):
		if cnetid and password:
			cnetid = ldap.filter.escape_filter_chars(cnetid)
			try:
				conn.simple_bind_s("uid=%s,ou=people,dc=uchicago,dc=edu" % cnetid, password)
			except ldap.INVALID_CREDENTIALS:
				return None
			try:
				user = User.objects.get(username=cnetid)
			except User.DoesNotExist:
				query = "(&(uid=%s)(objectclass=inetOrgPerson))" % (cnetid)
				result = conn.search_ext_s("dc=uchicago,dc=edu", ldap.SCOPE_SUBTREE, query)
				if result:
					user_data = result[0]
					user = User.objects.create_user(username=cnetid, email=user_data['mail'], first_name=user_data['givenName'], last_name=user_data['sn'])
					return user
		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None