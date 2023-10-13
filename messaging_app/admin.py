from django.contrib import admin
from .models import Message, MessageRelationship

admin.site.register(Message)
admin.site.register(MessageRelationship)
