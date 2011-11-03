from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def issue(i):
    url = reverse('issues_view', args=(i.project.name, i.id,))
    rep = '<a href="%s" title="%s">#%d</a>' % (url, i.title, i.id)
    if i.active:
        return rep
    else:
        return '<s>' + rep + '</s>'
