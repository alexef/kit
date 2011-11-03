from django.contrib import admin
from models import *

admin.site.register(Project)
admin.site.register(ProjectUser)
admin.site.register(Tracker)
admin.site.register(Category)
admin.site.register(Issue)
admin.site.register(Comment)