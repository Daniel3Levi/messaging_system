from rest_framework import serializers
from .models import Message
from django.contrib.auth.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        # Define the model for the serializer
        model = User

        # Specify the fields to include in the serialized data
        fields = ('username', 'email', 'password')

        # Extra kwargs for fields (in this case, making 'password' write-only)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Create a new user using the validated data
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    # (Write-only, not included in response)
    password = serializers.CharField(write_only=True)


class MessageSerializer(serializers.ModelSerializer):
    # Use 'sender.email' as the source
    sender = serializers.ReadOnlyField(source='sender.email')
    receiver = serializers.EmailField(source='receiver.email')

    class Meta:
        model = Message
        # Include all fields from the 'Message' model
        fields = '__all__'


