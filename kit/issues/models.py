from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

class ProjectUser(models.Model):
    ROLES = (('a', 'admin'), ('d', 'developer'), ('r', 'reporter'))
    user = models.ForeignKey(User)
    project = models.ForeignKey('Project')
    role = models.CharField(max_length=1, choices=ROLES, default='r')

    class Meta:
        unique_together = ('user', 'project')

    @classmethod
    def can_read(cls, user, project):
        try:
            exists = ProjectUser.objects.get(project=project, user=user)
            return True
        except:
            return user.is_superuser

    @classmethod
    def get_role(cls, user, project):
        try:
            exists = ProjectUser.objects.get(project=project, user=user)
            return exists.get_role_display()
        except:
            if user.is_superuser:
                return 'admin'
            return ''

    def get_absolute_url(self):
        return '/%s/manage/' % self.project.name

    def __unicode__(self):
        return self.user.__unicode__() + '-' + self.project.__unicode__()

class Project(models.Model):
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    public = models.BooleanField(default=False, blank=True)

    users = models.ManyToManyField(User, through=ProjectUser, blank=True)

    def __unicode__(self):
        return self.name

class Tracker(models.Model):
    name = models.CharField(max_length=32)

    def __unicode__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=64)
    project = models.ForeignKey(Project, blank=True, default=None, null=True)

    def __unicode__(self):
        return self.name

class Issue(models.Model):
    STATUSES = (('n', 'New'), ('c', 'Confirmed'), ('p', 'In progress'), ('r', 'Resolved'),
                ('f', 'Fixed'), ('i', 'Invalid'), ('w', "Won't fix"))
    tracker = models.ForeignKey(Tracker)
    status = models.CharField(max_length=1, choices=STATUSES, default='n', blank=True)
    reporter = models.ForeignKey(User, related_name='reporter')
    assigned = models.ForeignKey(User, related_name='assigned', default=None, blank=True, null=True)
    priority = models.IntegerField(default=20, blank=True) # 0 to 100
    category = models.ForeignKey(Category, blank=True, null=True, default=None)
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=200)
    text = models.TextField(max_length=1500, blank=True, default='')
    active = models.BooleanField(default=True, blank=True, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    dependencies = models.ManyToManyField('Issue', related_name='block', blank=True)
    subscribers = models.ManyToManyField(User, related_name='subscribed', blank=True)

    def get_priority_display(self):
        if self.priority < 20:
            return 'Low'
        elif self.priority < 50:
            return 'Normal'
        elif self.priority < 80:
            return 'Important'
        else:
            return 'Critical'

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('issues_view', args=(self.project.name, self.id))

    @property
    def comments(self):
        return self.comment_set.filter(reply_to=None).order_by('date')

    def save(self):
        is_new = (self.id is None)
        was_active = self.active
        if self.status in ('f', 'i', 'w'):
            self.active = False
            if was_active:
                if not self.assigned:
                    self.assigned = self.reporter
        else:
            self.active = True
        # pre save
        if is_new:
            super(Issue, self).save()
            self.subscribers.add(self.reporter)
            if self.assigned:
                self.subscribers.add(self.assigned)
        else:
            # assigned to
            had_assigned = Issue.objects.get(id=self.id).assigned
            if (had_assigned != self.assigned) and self.assigned:
                self.subscribers.add(self.assigned)

        super(Issue, self).save()
        
    def get_changes(self, initial, excludes=[]):
        changes = {}
        for field in self._meta.fields:
            if not (field.name in excludes):
                if field.value_from_object(self) != field.value_from_object(initial):
                    changes[field.verbose_name] = (field.value_from_object(self),
                                                       field.value_from_object(initial))
                    if field.flatchoices:
                        zero, value = changes[field.verbose_name]
                        value = dict(field.flatchoices).get(value, value)
                        changes[field.verbose_name] = (zero, value)
                    elif field.name in ('assigned', 'reporter'):
                        def get_user(field, obj):
                            id = field.value_from_object(obj)
                            try: return User.objects.get(id=id)
                            except: return None
                        changes[field.verbose_name] = (get_user(field, self),
                            get_user(field, initial))

        return changes

    def __unicode__(self):
        return u"#%d %s" % (self.id, self.title)

    def subscribers_display(self):
        return ','.join(map(unicode, self.subscribers.all()))

    def toggle_subscribe(self, user):
        if user in self.subscribers.all():
            self.subscribers.remove(user)
        else:
            self.subscribers.add(user)

class Comment(models.Model):
    issue = models.ForeignKey(Issue)
    reply_to = models.ForeignKey('Comment', related_name='reply', null=True, blank=True, default=None)
    author = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    text = models.TextField(max_length=2000)

    @property
    def children(self):
        return self.reply.all().order_by('date')

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse('issues_view', args=(self.issue.project.name, self.issue.id))

    @classmethod
    def changed(cls, user, issue, changes=None, text=''):
        if changes:
            msg = 'Changed: \n\n'
            for k,v in changes.iteritems():
                msg += ' * **%s**: %s \n' % (k, v[0])
        else:
            msg = text

        newcomm = cls.objects.create(issue=issue, author=user, text=msg)
        cls.alert(issue, user, text)

    @classmethod
    def alert(cls, issue, user, text, new=False):
        subject = '[%s] %s %s #%d' % (issue.project, user, 'changed' if not new else 'created', issue.id)
        mail_from = '@'.join((settings.EMAIL_HOST_USER, settings.EMAIL_HOST))
        if new:
            mail_to = [u.email for u in issue.project.users.all()]
        else:
            mail_to = [u.email for u in issue.subscribers.all()]
        mail_to = list(set(mail_to))
        text += '\n\n'+ settings.KIT_URL + issue.get_absolute_url()
        send_mail(subject, text, mail_from, mail_to, fail_silently=True)

    def __unicode__(self):
        return u"#%d %s: %s" % (self.issue.id, self.author, self.text[:50])