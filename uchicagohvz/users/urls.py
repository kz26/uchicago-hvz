from django.conf.urls import patterns, include, url
from django.contrib.auth.views import password_reset, password_reset_done, password_reset_confirm, password_reset_complete
from django.http import HttpResponse
from uchicagohvz.users.views import *
from uchicagohvz.users import mailing_list

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uchicagohvz.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^login/$', login, name="users|login"),
    url(r'^logout/$', logout, name="users|logout"),
    url(r'^profile/(?P<pk>[0-9]+)/$', ShowProfile.as_view(), name="users|profile"),
    url(r'^update_profile/$', UpdateProfile.as_view(), name="users|update_profile"),
    url(r'^register/$', RegisterUser.as_view(), name="users|register"),
    url(r'^ml/chatter_mailgun_mime$', mailing_list.ChatterMailingList.as_view()),
    url(r'^ml/test_mailgun_mime$', mailing_list.TestMailingList.as_view()),

    url(r'^password_reset/$', 
        password_reset, 
        {'post_reset_redirect' : '/users/password_reset_done/'},
        name="password_reset"),
    (r'^password_reset_done/$',
        password_reset_done),
    (r'^password_reset/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        'django.contrib.auth.views.password_reset_confirm', 
        {'post_reset_redirect' : '/users/password_done/'}),
    (r'^password_done/$', 
        password_reset_complete),
)
