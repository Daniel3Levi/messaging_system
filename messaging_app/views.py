from django.contrib.auth import authenticate, login
from rest_framework import permissions, status
from .tokens import create_jwt_pair
from rest_framework import viewsets
from .models import Message
from .serializers import UserRegistrationSerializer, UserLoginSerializer
from .serializers import MessageSerializer
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
class CreateMessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer = serializer.save(sender=self.request.user)
            response = {
                "detail": "New message send successfully.",
                "data": serializer.data
            }
            return Response(data=response, status=status.HTTP_201_CREATED)
        else:
            response = {
                "error": "An error occurred while sending the message.",
                "data": serializer.errors
            }
            return Response(data=response, status=response.status_code)


class ReadMessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        message = self.get_object()
        user = request.user

        if message.sender == user and message.sender_deleted:
            response = {
                "detail:" "Message has been deleted by the sender."
            }
            return Response(data=response, status=status.HTTP_410_GONE)

        if message.receivers.filter(user=user).exists():
            receiver = message.receivers.filter(user=user).first()
            if receiver and not receiver.is_read:
                receiver.is_read = True
                receiver.save()
        else:
            response = {
                "detail:" "The user is not in the receivers list of the message."
            }
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(message)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class DeleteMessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, pk=None):
        message = self.get_object()
        user = request.user

        if message.sender == user:
            message.sender_deleted = True
            message.save()
            response = {
                "detail": "Sender delete the message successfully."
            }
            return Response(data=response, status=status.HTTP_200_OK)

        if message.receivers.filter(user=user).exists():
            receiver = message.receivers.get(user=user)
            receiver.delete()
            response = {
                "detail": "Relationship removed from the message."
            }
            return Response(data=response, status=status.HTTP_200_OK)

        if message.receivers.count() == 0 and message.sender_deleted:
            message.delete()
            response = {
                "detail": "Message deleted by all users."
            }
            return Response(data=response, status=status.HTTP_204_NO_CONTENT)


class ReceivedMessagesViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(receivers__user=user)

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = Message.objects.filter(receivers__user=user)

        serializer = self.get_serializer(queryset, many=True)

        response = {
            'message_count': queryset.count(),
            'messages': serializer.data
        }

        return Response(data=response, status=status.HTTP_200_OK)


class SentMessagesViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(sender=user, sender_deleted=False)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data,
        }

        return Response(data=response, status=status.HTTP_200_OK)


class UnreadMessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(receivers__user=user, receivers__is_read=False)

    def list(self, request, *args, **kwargs):
        user = self.request.user
        queryset = Message.objects.filter(receivers__user=user, receivers__is_read=False)

        serializer = self.get_serializer(queryset, many=True)

        response = {
            'message_count': queryset.count(),
            'messages': serializer.data
        }

        return Response(data=response, status=status.HTTP_200_OK)

