from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from uchicagohvz.game.views import *
from uchicagohvz.game.api_views import *
from uchicagohvz.chat.views import *

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uchicagohvz.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', ListGames.as_view(), name='game|list'),
    url(r'^game/(?P<pk>[0-9]+)/$', ShowGame.as_view(), name='game|show'),
    url(r'^game/(?P<pk>[0-9]+)/leaderboard/$', Leaderboard.as_view(), name='game|leaderboard'),
    url(r'^game/(?P<pk>[0-9]+)/register/$', RegisterForGame.as_view(), name='game|register'),
    url(r'^game/(?P<pk>[0-9]+)/chat/$', ChatView.as_view(), name='game|chat'),
    url(r'^game/(?P<pk>[0-9]+)/chat/auth/$', ChatAuth.as_view(), name='game|chat|auth'),
    url(r'^game/(?P<pk>[0-9]+)/bite/$', EnterBiteCode.as_view(), name='game|bite'),
    url(r'^game/sms/$', SubmitCodeSMS.as_view(), name='game|sms'),
    url(r'^game/(?P<pk>[0-9]+)/code/$', SubmitAwardCode.as_view(), name='game|code'),
    url(r'^game/(?P<pk>[0-9]+)/data/kills/$', KillFeed.as_view(), name='game|data|kills'),
    url(r'^game/(?P<pk>[0-9]+)/data/humans-per-hour/$', HumansPerHour.as_view(), name='game|data|hph'),
    url(r'^game/(?P<pk>[0-9]+)/data/kills-by-tod/$', KillsByTimeOfDay.as_view(), name='game|data|kbtod'),
    url(r'^game/(?P<pk>[0-9]+)/data/humans-by-major/$', HumansByMajor.as_view(), name='game|data|hbm'),
    url(r'^game/(?P<pk>[0-9]+)/data/zombies-by-major/$', ZombiesByMajor.as_view(), name='game|data|zbm'),
    url(r'^game/(?P<pk>[0-9]+)/choose_squad/$', ChooseSquad.as_view(), name='game|choose_squad'),
    url(r'^kill/(?P<pk>[0-9]+)/$', ShowKill.as_view(), name='kill|show'),
    url(r'^kill/(?P<pk>[0-9]+)/annotate/$', AnnotateKill.as_view(), name='kill|annotate'),
    url(r'^player/(?P<pk>[0-9]+)/$', ShowPlayer.as_view(), name='player|show'),
    url(r'^player/(?P<pk>[0-9]+)/data/kills/$', PlayerKillFeed.as_view(), name='player|data|kills'),
	url(r'^squad/(?P<pk>[0-9]+)/$', ShowSquad.as_view(), name='squad|show'),
    url(r'^squad/(?P<pk>[0-9]+)/data/kills/$', SquadKillFeed.as_view(), name='squad|data|kills'),
    url(r'^feb-26-2015/$', TemplateView.as_view(template_name='game/feb-26-2015.html'), name='feb-26-2015-charlie-hebdo')
)
