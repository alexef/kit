from django.conf.urls.defaults import patterns, url
from views import IssueListView, IssueDetailView, IssueReportsView

urlpatterns = patterns('',
    url(r'list/$', IssueListView.as_view(), name='issues_list'),
    url(r'report/$', IssueReportsView.as_view(), name='issues_report'),
    url(r'view/(?P<pk>\d+)/$', IssueDetailView.as_view(), name='issues_view'),
)
