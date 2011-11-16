from django.contrib import admin
from models import *

class IssueAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'subscribers_display')

admin.site.register(Project)
admin.site.register(ProjectUser)
admin.site.register(Tracker)
admin.site.register(Category)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Comment)