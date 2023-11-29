from django.contrib import admin
from .models import Message, MessageRelationship, UserProfile

admin.site.register(Message)
admin.site.register(MessageRelationship)
admin.site.register(UserProfile)
