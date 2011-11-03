
def module(request):
    parts = request.path.split('/')
    if len(parts) > 2:
        return dict(module=parts[2])
    return dict(module='')