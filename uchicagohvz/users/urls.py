from django.conf.urls import patterns, include, url
from uchicagohvz.users.views import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uchicagohvz.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^login/$', login, name="users|login"),
    url(r'^logout/$', logout, name="users|logout"),
    url(r'^profile(?P<pk>[1-9]+)/$', ShowProfile.as_view(), name="users|profile"),
    url(r'^update_profile/$', UpdateProfile.as_view(), name="users|update_profile"),
    url(r'^register/$', RegisterUser.as_view(), name="users|register"),
)
