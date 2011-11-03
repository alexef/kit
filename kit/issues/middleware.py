from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from models import Project, ProjectUser

class Access:
    def process_view(self, request, view_func, view_args, view_kwargs):
        project = view_kwargs.get('project', None)
        if project is not None:
            project = get_object_or_404(Project, name=project)
            if project.public:
                return None
            else:
                if not request.user.is_authenticated():
                    return HttpResponseForbidden()
                elif not ProjectUser.can_read(request.user, project):
                    return HttpResponseForbidden()
        return None