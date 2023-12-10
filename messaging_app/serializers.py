from rest_framework import serializers
from .models import Message, UserMessage, CustomUser


# User Auth Serializers
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'profile_picture')
        extra_kwargs = {'password': {'write_only': True}}


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')


# Messages Serializers
class UserMessageSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)

    class Meta:
        model = UserMessage
        fields = ['user_email', 'is_recipient', 'is_sender', 'is_read']

    def get_user_email(self, user_message):
        if user_message.user:
            return user_message.user.email
        else:
            return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user_email'] = self.get_user_email(instance)
        return data


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.SerializerMethodField()
    recipients = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender_email', 'subject', 'body', 'creation_date', 'recipients']

    def get_sender_email(self, message_object):
        return message_object.sender.email

    def get_recipients(self, message):
        return [user.email for user in message.recipients.all()]


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', "email", 'profile_picture']



