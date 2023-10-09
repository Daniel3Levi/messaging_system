from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Message, Receivers

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

class ReceiversSerializer(serializers.ModelSerializer):

    receiver_email = serializers.EmailField(write_only=True, required=True)

    class Meta:
        model = Receivers
        fields = ('receiver_email', 'is_read')

    def create(self, validated_data):
        receiver_email = validated_data.pop('receiver_email')
        try:
            user = User.objects.get(email=receiver_email)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with email '{receiver_email}' does not exist.")
        validated_data['is_read'] = False
        receivers = Receivers.objects.create(user=user, **validated_data)
        return receivers


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.EmailField(source='sender.email', read_only=True)
    receivers = ReceiversSerializer(many=True)

    class Meta:
        model = Message
        fields = ('id', 'sender', 'subject', 'body', 'sender_deleted', 'receivers')
        read_only_fields = ['sender']

    def create(self, validated_data):
        receivers_data = validated_data.pop('receivers')
        message = Message.objects.create(**validated_data)

        for receiver_data in receivers_data:
            receiver_email = receiver_data.pop('receiver_email')
            user = User.objects.get(email=receiver_email)
            Receivers.objects.create(message=message, user=user, **receiver_data)

        return message

    def get_is_read(self, obj):
        user = self.context['request'].user
        try:
            receiver = obj.receivers.get(user=user)
            return receiver.is_read
        except Receivers.DoesNotExist:
            return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['receivers'] = [
            {
                "receiver_email": receiver.user.email,
                "is_read": receiver.is_read,
            }
            for receiver in instance.receivers.all()
        ]
        return representation
