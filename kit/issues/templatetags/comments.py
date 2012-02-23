import re
import hashlib
from django.template.loader import render_to_string
from django import template
register = template.Library()

@register.simple_tag
def do_comment(comm):
    return render_to_string('issues/comment.html', dict(c=comm, project=comm.issue.project))

@register.simple_tag
def gravatar(author):
    md5 = hashlib.md5(author.email).hexdigest()

    return 'http://www.gravatar.com/avatar/%s' % md5

@register.filter
def linkify(text, project=None):
    print project
    pat1 = re.compile(r"(^|[\n ])(\#(\d+))", re.DOTALL)
    text = pat1.sub(r'\1<a href="/%s/issues/view/\3">\2</a>' % project, text)
    pat = re.compile(r"(^|[\n ])(([\w]+?://[\w\#$%&~.\-;:=,?@\[\]+]*)(/[\w\#$%&~/.\-;:=,?@\[\]+]*)?)", re.IGNORECASE | re.DOTALL)
    text = pat.sub(r'\1<a href="\2" target="_blank">\3</a>', text)
    return text