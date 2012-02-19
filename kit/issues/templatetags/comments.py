from django.template.loader import render_to_string
from django import template
register = template.Library()

@register.simple_tag
def do_comment(comm):
    return render_to_string('issues/comment.html', dict(c=comm))