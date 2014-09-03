from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uchicagohvz.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('uchicagohvz.game.urls')),
    url(r'^users/', include('uchicagohvz.users.urls')),
    url(r'^contact/$', TemplateView.as_view(template_name='contact.html'), name='contact'),
    url(r'^faq/$', TemplateView.as_view(template_name='faq.html'), name='faq'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^terms/$', TemplateView.as_view(template_name='terms.html'), name='terms'),
    url(r'^search/', include('haystack.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
