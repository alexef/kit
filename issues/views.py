from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from models import Project, Issue, Tracker

class HomePage(TemplateView):
    template_name = 'issues/projects.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            projects = Project.objects.all()
        else:
            projects = Project.objects.filter(public=True)
        context = self.get_context_data(**kwargs)
        context['projects'] = projects
        return self.render_to_response(context)

class IssueListView(ListView):
    def get_queryset(self):
        project = get_object_or_404(Project, name__iexact=self.kwargs['project'])
        return Issue.objects.filter(project=project)

    def get_context_data(self, **kwargs):
        context = super(IssueListView, self).get_context_data(**kwargs)
        context['project'] = self.kwargs['project']
        context['trackers'] = Tracker.objects.all().order_by('-active', '-importance', '-date')
        return context

class IssueDetailView(DetailView):
    model = Issue

    def get_context_data(self, **kwargs):
        context = super(IssueDetailView, self).get_context_data(**kwargs)
        context['project'] = self.kwargs['project']
        return context

class IssueReportsView(TemplateView):
    template_name = 'issues/reports.html'

    def get_context_data(self, **kwargs):
        project = get_object_or_404(Project, name__iexact=kwargs['project'])

        context = dict(params=kwargs)
        context['users'] = User.objects.all()
        context['trackers'] = Tracker.objects.all()
        context['project'] = project

        def stats(user):
            class Stat:
                def __getitem__(self, item):
                    if item == 'reported':
                        return Issue.objects.filter(reporter=user).count()
                    elif item == 'assigned':
                        return Issue.objects.filter(assigned=user).count()
                    elif item == 'closed':
                        return Issue.objects.filter(assigned=user,active=False).count()
                    return None
            return Stat()
        User.stats = stats

        return context