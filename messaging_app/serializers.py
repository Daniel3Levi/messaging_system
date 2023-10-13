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
    class Meta:
        model = MessageRelationship
        fields = ['user', 'is_recipient', 'is_sender', 'is_read']


class MessageSerializer(serializers.ModelSerializer):
    message_relationship = MessageRelationshipSerializer(many=True)

    class Meta:
        model = Message
        fields = ['id', 'subject', 'body', 'creation_date', 'message_relationship']

    def create(self, validated_data):

        message = Message.objects.create(**validated_data)

        message_relationship_data = validated_data.pop('message_relationship', [])

        current_user = self.context['request'].user
        MessageRelationship.objects.create(
            message=message,
            user=current_user,
            is_sender=True,
            is_read=False,
            is_recipient=False
        )

        for relationship_data in message_relationship_data:
            MessageRelationship.objects.create(
                message=message,
                user=relationship_data['user'],
                is_sender=relationship_data['is_sender'],
                is_read=relationship_data['is_read'],
                is_recipient=relationship_data['is_recipient']
            )

        return message

