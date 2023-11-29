from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Message, MessageRelationship, UserProfile
from django.core.files.storage import default_storage
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

        # Set `required` to False for `username` and `password` if it's an update
        if self.instance is not None:
            self.fields['username'].required = False
            self.fields['password'].required = False

    def create(self, validated_data):
        profile_picture = validated_data.pop('profile_picture', None)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        if profile_picture:
            UserProfile.objects.create(user=user, profile_picture=profile_picture)

        return user

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if user != instance:
            raise serializers.ValidationError("You do not have permission to update this user.")

        profile_picture = validated_data.pop('profile_picture', None)

        # Update UserProfile instance
        user_profile, created = UserProfile.objects.get_or_create(user=instance)
        if profile_picture:
            # Path for the old profile picture
            if user_profile.profile_picture:
                old_picture_path = user_profile.profile_picture.name
                # Check if the old profile picture exists
                if default_storage.exists(old_picture_path):
                    # Deleting old picture
                    default_storage.delete(old_picture_path)
            # Set the new profile picture
            user_profile.profile_picture = profile_picture
            user_profile.save()

        instance.save()
        return instance


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
            print(user_email)
            try:
                user = User.objects.get(email=user_email)
                if user == sender_user:
                    sender_relationship.is_recipient = True
                    sender_relationship.save()
                elif user in recipients_users:
                    # How to handle duplicate recipient?
                    continue
                else:
                    MessageRelationship.objects.create(
                        message=message,
                        user=user,
                        is_sender=False,
                        is_read=False,
                        is_recipient=True
                    )
                    recipients_users.append(user)

            except User.DoesNotExist:
                failed_emails.append(user_email)

        message.recipients.add(*recipients_users)

        if failed_emails:
            raise serializers.ValidationError({
                "error": f"Users with emails {', '.join(failed_emails)} do not exist. "
                         f"However, the message was sent successfully to other recipients.",
                "message": message
            })

        elif message.recipients.count() == 0:
            message.delete()
            raise serializers.ValidationError({
                "error": f"Users with emails {', '.join(failed_emails)} do not exist. "
                         f"Try agine later."
            })

        else:
            return message


