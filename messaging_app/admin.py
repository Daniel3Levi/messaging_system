from django.contrib import admin
from .models import Message, UserMessage, CustomUser

admin.site.register(Message)
admin.site.register(CustomUser)
admin.site.register(UserMessage)
