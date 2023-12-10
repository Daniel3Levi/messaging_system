from django.db import models
from django.contrib.auth.models import AbstractUser
import os


def get_upload_path(instance, filename):
    return os.path.join('assets', 'profile_pictures', str(instance.pk), filename)


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True, blank=False, null=False)
    profile_picture = models.ImageField(upload_to=get_upload_path, blank=True, null=True)

    def __str__(self):
        return self.username


class Message(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=100)
    body = models.TextField()
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    recipients = models.ManyToManyField(CustomUser, related_name='received_messages')

    def __str__(self):
        return f"Subject: {self.subject}, Id: {self.id}"


class UserMessage(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="user_messages")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="messages")
    is_recipient = models.BooleanField(default=False)
    is_sender = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"User: {self.user}, Message: {self.message.id}"
