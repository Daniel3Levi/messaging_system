import os

from django.contrib.auth import authenticate, login
from django.core.files.storage import default_storage
from django.db.models import Q
from rest_framework import permissions, status
from .tokens import create_jwt_pair
from rest_framework import viewsets, filters
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer, UserMessageSerializer, \
    CustomUserSerializer
from .models import Message, UserMessage, CustomUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action


# User Views
class UserRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Create user
            user = CustomUser.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            profile_picture = request.data.get('profile_picture')
            if profile_picture:
                user.profile_picture = profile_picture
                user.save()

            return Response({'detail': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'User registration failed', 'error': serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)


class UserLoginViewSet(viewsets.ViewSet):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['post']

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


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_permissions(self):
        if self.action == 'list' or self.action == "retrieve":
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['patch'], url_path='update-profile-picture')
    def update_profile_picture(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            new_profile_picture = request.data.get('profile_picture')
            if new_profile_picture:
                old_picture_path = user.profile_picture.path
                if old_picture_path and default_storage.exists(old_picture_path):
                    default_storage.delete(old_picture_path)

            serializer.save()
            return Response({"detail": "Profile picture updated successfully.",
                             "user": serializer.data}, status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Somthing went wrong while updating profile picture.", "error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST)


# Messages Views
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        sender_user = self.request.user
        recipient_emails = self.request.data.get('recipients', [])
        message = serializer.save(sender=sender_user)

        sender_message = UserMessage.objects.create(
            message=message,
            user=sender_user,
            is_sender=True,
            is_read=False,
            is_recipient=False
        )

        recipients_users = []
        failed_emails = []

        for email in recipient_emails:
            try:
                user = CustomUser.objects.get(email=email)
                recipients_users.append(user)

                if email == sender_user.email:
                    sender_message.is_recipient = True
                    sender_message.save()
                    continue

                UserMessage.objects.create(
                    message=message,
                    user=user,
                    is_sender=(sender_user.email == email),
                    is_read=False,
                    is_recipient=True
                )

            except CustomUser.DoesNotExist:
                print(f"User with email {email} does not exist.")
                failed_emails.append(email)

        message.recipients.set(recipients_users)

        if not message.recipients.count():
            message.delete()
            return Response({"error": "No valid recipients found. Message not sent."}, status.HTTP_400_BAD_REQUEST)

        if failed_emails:
            message_serializer = self.get_serializer(message)

            return Response({
                "message": message_serializer.data,
                "failed_emails": failed_emails,
                "error": f"Users with emails {', '.join(failed_emails)} do not exist, "
                         f"the message was sent successfully to other recipients."}, status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return self.perform_create(serializer)

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]

    filter_fields = {
        'user_message': ['exact'],
        'user_message__is_sender': ['exact'],
        'user_message__is_recipient': ['exact'],
        'user_message__is_read': ['exact'],
    }

    ordering_fields = ['-creation_date', 'creation_date']
    search_fields = ['subject', 'body']

    def get_queryset(self):
        user = self.request.user
        filter_type = self.request.query_params.get('filter', None)
        is_read = self.request.query_params.get('is_read', None)

        queryset = Message.objects.filter(
            Q(user_messages__user=user, user_messages__is_sender=True) |
            Q(user_messages__user=user, user_messages__is_recipient=True)
        ).distinct()

        if filter_type == 'sent':
            queryset = queryset.filter(
                user_messages__user=user,
                user_messages__is_sender=True
            )
        elif filter_type == 'received':
            queryset = queryset.filter(
                user_messages__user=user,
                user_messages__is_recipient=True
            )

        if is_read == 'true':
            queryset = queryset.filter(
                user_messages__user=user,
                user_messages__is_read=True
            )
        elif is_read == 'false':
            queryset = queryset.filter(
                user_messages__user=user,
                user_messages__is_read=False
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = MessageSerializer(queryset, many=True)

        return Response({"number_of_messages": queryset.count(), "messages": serializer.data}, status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        message = self.get_object()
        user = request.user

        try:
            received_user_message = UserMessage.objects.get(message=message, user=user, is_recipient=True)
            if not received_user_message.is_read:
                received_user_message.is_read = True
                received_user_message.save()

        except UserMessage.DoesNotExist:
            return Response({
                "error": "Message not found."
            }, status=status.HTTP_404_NOT_FOUND)

        message_serializer = self.get_serializer(message)
        user_message_serializer = UserMessageSerializer(received_user_message)

        return Response({
            "detail": "Message read successfully.",
            "message": message_serializer.data,
            "user_message": user_message_serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        message = self.get_object()
        user = request.user

        try:
            user_message = UserMessage.objects.get(message=message, user=user)
            user_message.delete()

            remaining = UserMessage.objects.filter(message=message)
            if not remaining.exists():
                message.delete()
                return Response({"detail": "Message deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"detail": "Message deleted successfully."}, status=status.HTTP_403_FORBIDDEN)

        except UserMessage.DoesNotExist:

            return Response({"error": "Message not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['patch'], url_path='unread-message')
    def unread_message(self, request, pk=None):
        message = self.get_object()
        user = request.user

        try:
            user_message = UserMessage.objects.get(message=message, user=user, is_recipient=True)
            if user_message.is_read:
                user_message.is_read = False
                user_message.save()

                message_serializer = self.get_serializer(message)
                user_message_serializer = UserMessageSerializer(user_message)

                return Response({
                    "detail": "Message unread successfully.",
                    "message": message_serializer.data,
                    "user_message": user_message_serializer.data
                }, status=status.HTTP_200_OK)

        except UserMessage.DoesNotExist:
            return Response({'error': 'Message not found.'}, status=status.HTTP_404_NOT_FOUND)
