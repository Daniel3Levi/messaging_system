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

    class Meta:
        model = Message
        fields = ['id', 'subject', 'body', 'creation_date', 'message_relationship']

    def create(self, validated_data):
        message_relationship_data = validated_data.pop('message_relationship', [])
        current_user = self.context['request'].user

        message = Message.objects.create(**validated_data)

        sender_relationship = MessageRelationship.objects.create(
            message=message,
            user=current_user,
            is_sender=True,
            is_read=False,
            is_recipient=False
        )

        for relationship_data in message_relationship_data:
            user_email = relationship_data['user_email']
            if user_email == current_user.email:
                sender_relationship.is_recipient = True
                sender_relationship.save()
                continue

            user = User.objects.get(email=user_email)

            MessageRelationship.objects.create(
                message=message,
                user=user,
                is_sender=False,
                is_read=False,
                is_recipient=True
            )

        return message


