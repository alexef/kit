from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=64)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)

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
    active = models.BooleanField(default=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def get_priority_display(self):
        if self.priority < 20:
            return 'Low'
        elif self.priority < 50:
            return 'Normal'
        elif self.priority < 80:
            return 'Important'
        else:
            return 'Critical'

    def __unicode__(self):
        return u"#%d %s" % (self.id, self.title)