from django.db import models
from django.contrib.auth.models import User
import os


def get_upload_path(instance, filename):
    return os.path.join('Images', 'profile_pictures', str(instance.user.pk), filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to=get_upload_path, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Message(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=100)
    body = models.TextField()
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipients = models.ManyToManyField(User, related_name='received_messages')

    def __str__(self):
        return 'Subject:' + self.subject


class MessageRelationship(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_relationship")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_relationship")
    is_recipient = models.BooleanField(default=False)
    is_sender = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
