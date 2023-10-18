from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Message, MessageRelationship


# User Auth Serializers
class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


# Messages Serializers
class MessageRelationshipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(write_only=True)

    class Meta:
        model = MessageRelationship
        fields = ['user_email', 'is_recipient', 'is_sender', 'is_read']

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

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

    def get_sender_email(self, obj):
        return obj.sender.email

    def get_recipients(self, obj):
        return [user.email for user in obj.recipients.all()]

    def create(self, validated_data):
        message_relationship_data = validated_data.pop('message_relationship', [])
        sender_user = self.context['request'].user

        message = Message.objects.create(sender=sender_user, **validated_data)
        recipients_users = []
        failed_emails = []

        # Create a MessageRelationship for the sender initially with is_sender=True
        sender_relationship = MessageRelationship.objects.create(
            message=message,
            user=sender_user,
            is_sender=True,
            is_read=False,
            is_recipient=False
        )

        for relationship_data in message_relationship_data:
            user_email = relationship_data['user_email']
            try:
                user = User.objects.get(email=user_email)
                recipients_users.append(user)
                if user == sender_user:
                    sender_relationship.is_recipient = True
                    sender_relationship.save()
                else:
                    MessageRelationship.objects.create(
                        message=message,
                        user=user,
                        is_sender=False,
                        is_read=False,
                        is_recipient=True
                    )
            except User.DoesNotExist:
                failed_emails.append(user_email)

        message.recipients.add(*recipients_users)

        if failed_emails:
            raise serializers.ValidationError({
                "user_email": f"Users with emails {', '.join(failed_emails)} do not exist. "
                              f"However, the message was sent successfully to other recipients."
            })

        return message

