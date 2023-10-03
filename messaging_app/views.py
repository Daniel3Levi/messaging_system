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
    # Use the serializer for user registration
    serializer_class = UserRegistrationSerializer

    # Allow any user, including unauthenticated users, to access this view
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Call the parent class's create method to perform user registration
        response = super().create(request, *args, **kwargs)

        # Check if the registration was successful (HTTP status code 201 Created)
        if response.status_code == status.HTTP_201_CREATED:
            # Customize the response message
            response = {
                'detail': 'User registered successfully'
            }
            # Return the customized response with a 201 status code
            return Response(data=response, status=status.HTTP_201_CREATED)
        else:
            # Get the validation errors from the serializer
            serializer_errors = response.data

            # Customize the response message
            response = {
                'detail': 'User registration failed',
                'error': serializer_errors
            }
            return Response(data=response, status=response.status_code)


class UserLoginViewSet(viewsets.ViewSet):
    # Set the serializer class for login
    serializer_class = UserLoginSerializer

    # Allow any user, including unauthenticated users, to access this view
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Get the username and password from the request data
        username = request.data.get('username')
        password = request.data.get('password')

        # Authenticate the user with built-in Django function
        user = authenticate(request, username=username, password=password)

        if user:
            # If authentication is successful, log in the user
            login(request, user)

            # Generate or retrieve a JWT token for the user
            tokens = create_jwt_pair(user)

            # Customize the response for a successful login
            response = {
                'detail': 'User logged in successfully',
                'token': tokens
            }
            return Response(data=response, status=status.HTTP_200_OK)
        else:
            # If authentication fails
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
            # Resolve the receiver user object based on their email address
            receiver_user = User.objects.get(email=receiver_email)

            # Check if the sender is the same as the receiver
            if receiver_user == self.request.user:
                response = {
                    'error': 'Sender and receiver cannot be the same'
                }
                return Response(data=response, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                # Set the sender and receiver and create the message
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
        # Filter messages to only allow the user to update messages they have received
        return Message.objects.filter(receiver=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the user is the receiver of the message
        if instance.receiver != self.request.user:
            # If the user is not the receiver, return a 403 Forbidden response
            response = {
                'detail': 'Something went wrong while trying to retrieve the message.',
                'error': 'You can only mark messages as read if you are the receiver.'
            }
            return Response(data=response, status=status.HTTP_403_FORBIDDEN)

        # Mark the message as read
        instance.is_read = True
        instance.save()

        # Serialize the updated message
        updated_message = self.get_serializer(instance).data

        # Create a success response with the updated message data
        response = {
            'detail': 'Message updated successfully.',
            'data': updated_message
        }
        return Response(data=response, status=status.HTTP_200_OK)


class UnreadMessagesViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Get the queryset of unread messages for the current user
        queryset = self.get_queryset().filter(is_read=False)

        # Serialize the unread messages
        serializer = self.get_serializer(queryset, many=True)

        # Customize the response data
        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data
        }

        # Return a customized response
        return Response(data=response, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Filter messages to only include messages received by the user
        return Message.objects.filter(receiver=self.request.user)


class SentMessagesViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Get the queryset of sent messages by the current user
        queryset = self.get_queryset()

        # Serialize the sent messages
        serializer = self.get_serializer(queryset, many=True)

        # Customize the response data
        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data
        }

        # Return a customized response
        return Response(data=response, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Filter messages to only include messages sent by the user
        return Message.objects.filter(sender=self.request.user)


class ReceivedMessagesViewSet(viewsets.ModelViewSet):

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Get the queryset of received messages for the current user
        queryset = self.get_queryset()

        # Serialize the received messages
        serializer = self.get_serializer(queryset, many=True)

        # Customize the response data
        response = {
            'messages_count': queryset.count(),
            'messages': serializer.data
        }

        # Return a customized response
        return Response(data=response, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Filter messages to only include messages received by the user
        return Message.objects.filter(receiver=self.request.user)
