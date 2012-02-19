from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from kit.issues.models import Comment, Project

class ProjectStream(TemplateView):
    template_name = 'activity/stream.html'

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, name__iexact=kwargs['project'])
        if not request.user.is_authenticated() and not project.public:
            raise Http404()

        context = self.get_context_data(**kwargs)
        comments = Comment.objects.filter(issue__project=project).order_by('-date')[:100]
        if comments:
            date = comments[0].date
            day_data = []
            data = []
            for c in comments:
                if c.date.date() == date.date():
                    day_data.append(c)
                else:
                    data.append((date, day_data))
                    date = c.date
                    day_data = [c]
            if day_data:
                data.append((date, day_data))
            context['data'] = data
        else:
            context['data'] = []
        return self.render_to_response(context)
