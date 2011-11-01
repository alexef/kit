from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import get_object_or_404
from models import Project, Issue, Tracker

class HomePage(TemplateView):
    template_name = 'issues/projects.html'

    def get_context_data(self, **kwargs):
        return {'params': kwargs, 'projects': Project.objects.all()}

class IssueListView(ListView):
    def get_queryset(self):
        project = get_object_or_404(Project, name__iexact=self.kwargs['project'])
        return Issue.objects.filter(project=project)

    def get_context_data(self, **kwargs):
        context = super(IssueListView, self).get_context_data(**kwargs)
        context['project'] = self.kwargs['project']
        context['trackers'] = Tracker.objects.all()
        return context

class IssueDetailView(DetailView):
    model = Issue

    def get_context_data(self, **kwargs):
        context = super(IssueDetailView, self).get_context_data(**kwargs)
        context['project'] = self.kwargs['project']
        return context