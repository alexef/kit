from kit.issues.models import Project, ProjectUser

def module(request):
    parts = request.path.split('/')
    project, module, action = '', '', ''
    if len(parts) > 1:
        project = parts[1]
    if len(parts) > 2:
        module=parts[2]
    if len(parts) > 3:
        action = parts[3]

    try:
        project = Project.objects.get(name__iexact=project)
    except Project.DoesNotExist:
        project = None

    role = ProjectUser.get_role(request.user, project)
    return dict(module=module, project=project, action=action, role=role)