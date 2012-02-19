from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django import forms
from models import Project, ProjectUser, Issue, Tracker, Comment, UserPreference

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
        form = IssueForm(instance=self.object)
        form.bind_fields()
        context['modifyform'] = form
        context['commentform'] = CommentForm(initial={'issue':self.object})
        context['is_subscribed'] = (self.user in self.object.subscribers.all())
        return context

class ToggleSubscribe(DetailView):
    def get(self, request, **kwargs):
        user = request.user
        issue = get_object_or_404(Issue, pk=kwargs['pk'])
        issue.toggle_subscribe(user)
        return HttpResponseRedirect(issue.get_absolute_url())

class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        exclude = ('subscribers', )
        
    def bind_fields(self, project=None):
        if project is None:
            if not self.instance:
                return
            else:
                project = self.instance.project
        self.fields['dependencies'].queryset = project.issue_set
        self.fields['category'].queryset = project.category_set
        self.fields['assigned'].queryset = project.users
        self.fields['reporter'].queryset = project.users

class IssueEdit(UpdateView):
    model = Issue
    form_class = IssueForm

    def post(self, request, *args, **kwargs):
        self.user = request.user
        return super(UpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        object = Issue.objects.get(pk=self.object.pk)
        new_object = form.save(commit=False)

        # get differences
        changes = new_object.get_changes(object, dict(dependencies=form.cleaned_data['dependencies']))

        new_object.save()
        form.save_m2m()
        if changes:
            Comment.changed(self.user, object, changes)
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

    def get_form(self, form_class):
        form = form_class(**self.get_form_kwargs())
        project = get_object_or_404(Project, name__iexact=self.kwargs['project'])
        form.fields['category'].queryset = project.category_set
        return form

    def post(self, request, *args, **kwargs):
        self.user = request.user
        return super(IssueCreate, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        text = 'Created new %s: %s\n\n%s' % (self.object.tracker, self.object.title, self.object.text)
        Comment.alert(self.object, self.user, text, new=True)
        return HttpResponseRedirect(self.object.get_absolute_url())

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.kwargs = kwargs
        return super(IssueCreate, self).dispatch(*args, **kwargs)

    form_class = IssueCreateForm
    model = Issue

class IssueReportsView(TemplateView):
    template_name = 'issues/reports.html'

    def get_context_data(self, **kwargs):
        project = get_object_or_404(Project, name__iexact=kwargs['project'])

        context = dict(params=kwargs)
        context['users'] = project.users.all()
        context['trackers'] = Tracker.objects.all()

        def stats(user):
            class Stat:
                def __getitem__(self, item):
                    if item == 'reported':
                        return Issue.objects.filter(reporter=user, project=project).count()
                    elif item == 'assigned':
                        return Issue.objects.filter(assigned=user, project=project).count()
                    elif item == 'closed':
                        return Issue.objects.filter(assigned=user, active=False, project=project).count()
                    return None
            return Stat()
        User.stats = stats

        return context

class CommentCreate(CreateView):
    model = Comment

    def post(self, request, *args, **kwargs):
        self.user = request.user
        return super(CommentCreate, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        text = 'New comment: \n\n' + self.object.text
        Comment.alert(self.object.issue, self.user, text)
        return HttpResponseRedirect(self.get_success_url())

class PUCreate(CreateView):
    model = ProjectUser

class PUUpdate(UpdateView):
    model = ProjectUser

class Preferences(TemplateView):
    template_name = 'issues/preferences.html'

    class PrefsForm(forms.Form):
        subscribe_created = forms.BooleanField(initial=True, required=False)
        subscribe_updated = forms.BooleanField(initial=True, required=False)

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        return super(Preferences, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        project = get_object_or_404(Project, name__iexact=kwargs['project'])
        user = self.request.user

        prefs = {}
        for up in UserPreference.objects.filter(project=project, user=user).all():
            prefs[up.name] = up.get_value()

        return {'prefsform': Preferences.PrefsForm(initial=prefs)}

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, name__iexact=kwargs['project'])
        form = Preferences.PrefsForm(request.POST)
        if form.is_valid():
            for k,v in form.cleaned_data.iteritems():
                up, new = UserPreference.objects.get_or_create(project=project, user=request.user, name=k)
                up.set_value(v)

        return HttpResponseRedirect(reverse('preferences', args=(project,)))