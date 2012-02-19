from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('',
    url(r'$', ProjectStream.as_view(), name='activity_project'),
)
