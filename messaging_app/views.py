from django.contrib.auth import authenticate, login
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import action
from .tokens import create_jwt_pair
from rest_framework import viewsets, filters
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from .models import Message, MessageRelationship
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser


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
        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            response = {
                'detail': 'User registered successfully'
            }
            return Response(data=response, status=status.HTTP_201_CREATED)
        else:
            serializer_errors = response.data
            response = {
                'detail': 'User registration failed',
                'error': serializer_errors
            }
            return Response(data=response, status=response.status_code)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            response = {
                'detail': 'User profile updated successfully'
            }
            return Response(data=response, status=status.HTTP_200_OK)
        else:
            serializer_errors = response.data
            response = {
                'detail': 'Update user profile failed',
                'error': serializer_errors
            }
        return response


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
