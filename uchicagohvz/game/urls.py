from django.conf.urls import patterns, include, url
from uchicagohvz.game.views import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uchicagohvz.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', ListGames.as_view(), name="games|list"),
)
