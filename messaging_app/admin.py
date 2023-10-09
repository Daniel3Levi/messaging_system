from django.contrib import admin
from .models import Message, Receivers

# Register Message model to django admin site.
admin.site.register(Message)

admin.site.register(Receivers)
