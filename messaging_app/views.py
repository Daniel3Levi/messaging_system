from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework import permissions, status
from rest_framework.permissions import AllowAny
from .models import Message
from .tokens import create_jwt_pair
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from rest_framework import viewsets
from rest_framework.response import Response


# User Views

class UserRegistrationViewSet(viewsets.ModelViewSet):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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
                'detail': 'Something went wrong while trying to log in.',
                'errors': {
                    'authentication': 'Invalid credentials'
                }
            }
            return Response(data=response, status=status.HTTP_401_UNAUTHORIZED)


# Messages Views

class NewMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Set the sender as the logged-in user
        serializer.save(sender=self.request.user)

    def create(self, request, *args, **kwargs):
        receiver_email = request.data.get('receiver', '')

        try:
            receiver_user = User.objects.get(email=receiver_email)

            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(sender=self.request.user, receiver=receiver_user)
                headers = self.get_success_headers(serializer.data)
                return Response(data=serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            response = {
                'error': 'Receiver does not exist'
            }
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)


class ReadMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(receiver=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.receiver != self.request.user:
            response = {
                'detail': 'Something went wrong while trying to retrieve the message.',
                'error': 'You can only mark messages as read if you are the receiver.'
            }
            return Response(data=response, status=status.HTTP_403_FORBIDDEN)
        elif instance.is_read:
            message = self.get_serializer(instance).data
            response = {
                'data': message
            }
            return Response(data=response, status=status.HTTP_200_OK)

        instance.is_read = True
        instance.save()
        updated_message = self.get_serializer(instance).data
        response = {
            'detail': 'Message updated successfully.',
            'data': updated_message
        }
        return Response(data=response, status=status.HTTP_202_ACCEPTED)


class UnreadMessagesViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data
        }
        return Response(data=response, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Message.objects.filter(receiver=self.request.user)


class SentMessagesViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data
        }
        return Response(data=response, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user)


class ReceivedMessagesViewSet(viewsets.ModelViewSet):

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data
        }
        return Response(data=response, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Message.objects.filter(receiver=self.request.user)
