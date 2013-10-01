from django.conf.urls import patterns, include, url
from uchicagohvz.game.views import *
from uchicagohvz.game.data_apis import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uchicagohvz.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', ListGames.as_view(), name="game|list"),
    url(r'^game/(?P<pk>[0-9]+)/$', ShowGame.as_view(), name="game|show"),
    url(r'^game/(?P<pk>[0-9]+)/register/$', RegisterForGame.as_view(), name="game|register"),
    url(r'^game/(?P<pk>[0-9]+)/bite/$', SubmitBiteCode.as_view(), name="game|bite"),
    url(r'^game/(?P<pk>[0-9]+)/code/$', SubmitAwardCode.as_view(), name="game|code"),
    url(r'^game/(?P<pk>[0-9]+)/data/hph/$', HumansPerHour.as_view(), name="game|data|HPH"),
)
