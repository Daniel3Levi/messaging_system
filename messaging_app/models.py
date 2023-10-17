from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=100)
    body = models.TextField()

    def __str__(self):
        return 'Subject:' + self.subject


class MessageRelationship(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_relationship")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_relationship")
    is_recipient = models.BooleanField(default=False)
    is_sender = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
