from django.contrib.auth import authenticate, login
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import action
from .tokens import create_jwt_pair
from rest_framework import viewsets
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from .models import Message, MessageRelationship
from rest_framework.response import Response


# User Views
class UserRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

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


class UserLoginViewSet(viewsets.ViewSet):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
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
    serializer_class = MessageSerializer

    @action(detail=True, methods=['put'], url_path='update-is-read')
    def update_is_read(self, request):
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
    def delete_relationship(self, request):
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

    def get_queryset(self):
        user = self.request.user

        filter_type = self.request.query_params.get('filter', None)

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
        elif filter_type == 'received_unread':
            queryset = queryset.filter(
                message_relationship__user=user,
                message_relationship__is_recipient=True,
                message_relationship__is_read=False
            )
        elif filter_type == 'received_read':
            queryset = queryset.filter(
                message_relationship__user=user,
                message_relationship__is_recipient=True,
                message_relationship__is_read=True
            )

        return queryset
