from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('',
    url(r'list/$', IssueListView.as_view(), name='issues_list'),
    url(r'report/$', IssueReportsView.as_view(), name='issues_report'),
    url(r'view/(?P<pk>\d+)/$', IssueDetailView.as_view(), name='issues_view'),
    url(r'edit/(?P<pk>\d+)/$', IssueEdit.as_view(), name='issues_edit'),
    url(r'new/$', IssueCreate.as_view(), name='issues_new'),
    url(r'prefs/$', Preferences.as_view(), name='preferences'),

    url(r'toggle-subscribe/(?P<pk>\d+)/$', ToggleSubscribe.as_view(), name='toggle_subscribe'),
    url(r'comment/$', CommentCreate.as_view(), name='comment_new'),
)
