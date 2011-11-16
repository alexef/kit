from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django import forms
from models import Project, ProjectUser, Issue, Tracker, Comment

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

class ManageProject(TemplateView):
    template_name = 'issues/project_manage.html'

    def get_context_data(self, **kwargs):
        context = super(ManageProject, self).get_context_data(**kwargs)
        class PUForm(forms.ModelForm):
            class Meta:
                model = ProjectUser
                widgets = {'project': forms.HiddenInput}
        project = get_object_or_404(Project, name__iexact=self.kwargs['project'])
        context['puform'] = PUForm(initial={'project': project})
        return context

class IssueListView(ListView):
    def get_queryset(self):
        project = get_object_or_404(Project, name__iexact=self.kwargs['project'])
        return Issue.objects.filter(project=project).order_by('tracker', '-active', 'status', '-date_updated')

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        # apply filters
        status = request.GET.get('status', 'open')
        if status:
            if status == 'open':
                self.object_list = self.object_list.filter(active=True)
            elif status == 'closed':
                self.object_list = self.object_list.filter(active=False)
        context = self.get_context_data(object_list=self.object_list, status=status)
        return self.render_to_response(context)

class IssueDetailView(DetailView):
    model = Issue

    def get(self, request, **kwargs):
        self.user = request.user
        return super(IssueDetailView, self).get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IssueDetailView, self).get_context_data(**kwargs)
        class CommentForm(forms.ModelForm):
            class Meta:
                model = Comment
                fields = ('text', 'issue')
                widgets = {'issue': forms.HiddenInput}
        context['commentform'] = CommentForm(initial={'issue':self.object})
        context['is_subscribed'] = (self.user in self.object.subscribers.all())
        return context

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        exclude = ('subscribers', )

class IssueEdit(UpdateView):
    model = Issue
    form_class = IssueForm

    def post(self, request, *args, **kwargs):
        self.user = request.user
        return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        new_object = form.save(commit=False)
        object = Issue.objects.get(pk=self.object.pk)
        # get differences
        changes = new_object.get_changes(object)
        if changes:
            Comment.changed(self.user, object, changes)
        new_object.save()
        return HttpResponseRedirect(self.get_success_url())

class NoInput(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        return ''

class IssueCreate(CreateView):
    class IssueCreateForm(forms.ModelForm):
        class Meta:
            fields = ('tracker', 'priority', 'category', 'title', 'text', 'reporter', 'project')
            widgets = {'reporter': NoInput, 'project': NoInput}
            model = Issue

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(IssueCreate, self).dispatch(*args, **kwargs)

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

class PUCreate(CreateView):
    model = ProjectUser

class PUUpdate(UpdateView):
    model = ProjectUser