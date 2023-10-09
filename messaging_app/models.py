from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    subject = models.CharField(max_length=100)
    creation_date = models.DateTimeField(auto_now_add=True)
    sender_deleted = models.BooleanField(default=False)

    def __str__(self):
        return 'Subject:' + self.subject


class Receivers(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="receivers")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    is_read = models.BooleanField(default=False)

