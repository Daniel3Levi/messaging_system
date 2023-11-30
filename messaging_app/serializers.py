from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Message, MessageRelationship, UserProfile
from django.core.validators import FileExtensionValidator


# User Auth Serializers
class UserRegistrationSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(write_only=True, required=False, use_url=True,
                                             validators=[FileExtensionValidator(allowed_extensions=
                                                                                ['jpg', 'jpeg', 'png', 'gif'])])

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'profile_picture')
        extra_kwargs = {'password': {'write_only': True}}

    def __init__(self, *args, **kwargs):
        super(UserRegistrationSerializer, self).__init__(*args, **kwargs)

        # Set required to False for username and password if it's an update
        if self.instance is not None:
            self.fields['username'].required = False
            self.fields['password'].required = False


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


# Messages Serializers
class MessageRelationshipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)

    class Meta:
        model = MessageRelationship
        fields = ['user_email', 'is_recipient', 'is_sender', 'is_read']

    def get_user_email(self, message_relationship):
        if message_relationship.user:
            return message_relationship.user.email
        else:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user_email'] = self.get_user_email(instance)
        return data


class MessageSerializer(serializers.ModelSerializer):
    message_relationship = MessageRelationshipSerializer(many=True)
    sender_email = serializers.SerializerMethodField()
    recipients = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender_email', 'subject', 'body', 'creation_date', 'recipients', 'message_relationship']

    def get_sender_email(self, message_object):
        return message_object.sender.email

    def get_recipients(self, message_object):
        emails = []
        for user in message_object.recipients.all():
            emails.append(user.email)
        return emails
