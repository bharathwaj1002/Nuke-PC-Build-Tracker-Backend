from django.contrib import admin
from .models import Build, Component, CustomUser, StatusLog, Checklist, InvoiceStatus

admin.site.register(Build)
admin.site.register(Component)
admin.site.register(StatusLog)
admin.site.register(Checklist)
admin.site.register(InvoiceStatus)
admin.site.register(CustomUser)  # Register User model for admin access