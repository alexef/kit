from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django import forms
from models import Project, Issue, Tracker, Comment

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
        return Issue.objects.filter(project=project).order_by('tracker', '-active', 'status', '-date_updated')

class IssueDetailView(DetailView):
    model = Issue

    def get_context_data(self, **kwargs):
        context = super(IssueDetailView, self).get_context_data(**kwargs)
        class CommentForm(forms.ModelForm):
            class Meta:
                model = Comment
                fields = ('text', 'issue')
                widgets = {'issue': forms.HiddenInput}
        context['commentform'] = CommentForm(initial={'issue':self.object})
        return context

class IssueEdit(UpdateView):
    model = Issue

class NoInput(forms.HiddenInput):
    def render(self, name, value,attrs=None):
        return ''

class IssueCreate(CreateView):
    class IssueCreateForm(forms.ModelForm):
        class Meta:
            fields = ('tracker', 'priority', 'category', 'title', 'text', 'reporter', 'project')
            widgets = {'reporter': NoInput, 'project': NoInput}
            model = Issue

    form_class = IssueCreateForm
    model = Issue

class IssueReportsView(TemplateView):
    template_name = 'issues/reports.html'

    def get_context_data(self, **kwargs):
        project = get_object_or_404(Project, name__iexact=kwargs['project'])

        context = dict(params=kwargs)
        context['users'] = User.objects.all()
        context['trackers'] = Tracker.objects.all()

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

class CommentCreate(CreateView):
    model = Comment
