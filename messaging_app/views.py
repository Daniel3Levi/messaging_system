from django.contrib.auth import authenticate, login
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import action
from .tokens import create_jwt_pair
from rest_framework import viewsets, filters
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from .models import Message, MessageRelationship, UserProfile
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage


# User Views
class UserRegistrationViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [permissions.IsAdminUser]
        elif self.action == 'update':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    serializer_class = UserRegistrationSerializer
    parser_classes = [FormParser, MultiPartParser]

    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            profile_picture = request.data.get('profile_picture')
            if profile_picture:
                UserProfile.objects.create(user=user, profile_picture=profile_picture)

            return Response({'detail': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'User registration failed', 'error': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        if request.user != user:
            return Response({'detail': 'You do not have permission to update this user.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()

            profile_picture = request.data.get('profile_picture')
            if profile_picture:
                user_profile_instance, created = UserProfile.objects.get_or_create(user=user)
                image_file = user_profile_instance.profile_picture
                if image_file:
                    old_picture_path = image_file.name
                    if default_storage.exists(old_picture_path):
                        default_storage.delete(old_picture_path)
                user_profile_instance.profile_picture = profile_picture
                user_profile_instance.save()

            return Response({'detail': 'User profile updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Update user profile failed', 'error': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class UserLoginViewSet(viewsets.ViewSet):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            # Generate or retrieve a JWT token for the user
            tokens = create_jwt_pair(user)
            response = {
                'detail': 'User logged in successfully',
                'token': tokens
            }
            return Response(data=response, status=status.HTTP_200_OK)
        else:
            response = {
                'detail': 'Something went wrong while trying to logged in.',
                'errors': {
                    'authentication': 'Invalid credentials'
                }
            }
            return Response(data=response, status=status.HTTP_401_UNAUTHORIZED)


# Messages Views
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_permissions(self):
        if self.action == 'delete' or self.action == 'update':
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        data = request.data
        sender_user = request.user
        message_relationship_data = data.pop('message_relationship', [])

        message = Message.objects.create(sender=sender_user, **data)
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
            user_email = relationship_data.get('user_email')
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
            return Response({
                "error": f"Users with emails {', '.join(failed_emails)} do not exist. "
                         f"However, the message was sent successfully to other recipients.",
                "message": message.id
            }, status=status.HTTP_400_BAD_REQUEST)

        elif message.recipients.count() == 0:
            message.delete()
            return Response({
                "error": "No valid recipients found. Message not sent."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]

    filter_fields = {
        'message_relationship__user': ['exact'],
        'message_relationship__is_sender': ['exact'],
        'message_relationship__is_recipient': ['exact'],
        'message_relationship__is_read': ['exact'],
    }

    ordering_fields = ['-creation_date', 'creation_date']
    search_fields = ['subject', 'body']

    def get_queryset(self):
        user = self.request.user
        filter_type = self.request.query_params.get('filter', None)
        is_read = self.request.query_params.get('is_read', None)

        queryset = Message.objects.filter(
            Q(message_relationship__user=user, message_relationship__is_sender=True) |
            Q(message_relationship__user=user, message_relationship__is_recipient=True)
        ).distinct()

        if filter_type == 'sent':
            queryset = queryset.filter(
                message_relationship__user=user,
                message_relationship__is_sender=True
            )
        elif filter_type == 'received':
            queryset = queryset.filter(
                message_relationship__user=user,
                message_relationship__is_recipient=True
            )

        if is_read == 'true':
            queryset = queryset.filter(
                message_relationship__user=user,
                message_relationship__is_read=True
            )
        elif is_read == 'false':
            queryset = queryset.filter(
                message_relationship__user=user,
                message_relationship__is_read=False
            )

        return queryset

    @action(detail=True, methods=['put'], url_path='update-is-read')
    def update_is_read(self, request, pk=None):
        message = self.get_object()
        user = request.user

        try:
            received_relationship = MessageRelationship.objects.get(message=message, user=user, is_recipient=True)
            received_relationship.is_read = True
            received_relationship.save()
            response = {
                'detail': 'Read message successfully.'
            }
            return Response(data=response, status=status.HTTP_200_OK)
        except MessageRelationship.DoesNotExist:
            response = {
                'detail': 'Message not found.'
            }
            return Response(data=response, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['delete'], url_path='delete-relationship')
    def delete_relationship(self, request, pk=None):
        message = self.get_object()
        user = request.user
        try:
            message_relationship = MessageRelationship.objects.get(message=message, user=user)
            if message_relationship.is_sender or message_relationship.is_recipient:
                message_relationship.delete()

                remaining_relationships = MessageRelationship.objects.filter(message=message)
                if not remaining_relationships.exists():
                    message.delete()

                response = {
                    "detail": "Message deleted successfully."
                }
                return Response(data=response, status=status.HTTP_204_NO_CONTENT)
            else:
                response = {
                    "detail": "Access to the message denied."
                }
                return Response(data=response, status=status.HTTP_403_FORBIDDEN)
        except MessageRelationship.DoesNotExist:
            response = {
                "detail": "Message not found."
            }
            return Response(data=response, status=status.HTTP_404_NOT_FOUND)
