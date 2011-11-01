from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

from kit.issues.views import HomePage

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'kit.views.home', name='home'),
    # url(r'^kit/', include('kit.foo.urls')),

    url(r'^$', HomePage.as_view(), name='projects_list'),
    url(r'^(?P<project>.+)/issues/', include('kit.issues.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
