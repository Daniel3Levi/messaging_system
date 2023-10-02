from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Message
from .serializers import UserRegistrationSerializer, UserLoginSerializer, MessageSerializer
from rest_framework.authtoken.models import Token


# User Views


class UserRegistrationView(generics.CreateAPIView):
    # Define the queryset (usually not needed for registration)
    queryset = User.objects.all()

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


class UserLoginView(generics.GenericAPIView):
    # Set the serializer class for login
    serializer_class = UserLoginSerializer

    # Allow any user, including unauthenticated users, to access this view
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # Get the username and password from the request data
        username = request.data.get('username')
        password = request.data.get('password')

        # Authenticate the user with built-in django function
        user = authenticate(request, username=username, password=password)

        if user:
            # If authentication is successful, log in the user
            login(request, user)

            # Generate or retrieve a token for the user
            token, created = Token.objects.get_or_create(user=user)

            # Customize the response for a successful login
            response = {
                'detail': 'User logged in successfully',
                'token': token.key
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


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Set the sender as the logged-in user
        serializer.validated_data['sender'] = self.request.user

        receiver_email = self.request.data.get('receiver', '')

        try:
            # Resolve the receiver user object based on their email address
            receiver_user = User.objects.get(email=receiver_email)
            serializer.validated_data['receiver'] = receiver_user

            if serializer.is_valid():
                # Create the message
                serializer.save()
                return Response(data=serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            response = {
                'error': 'Receiver does not exist'
            }
            return Response(data=response, status=status.HTTP_400_BAD_REQUEST)


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
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
                'detail': 'Somthing went wrong while trying to retrieve the message. ',
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


from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Message
from .serializers import MessageSerializer


class UnreadMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Get the queryset of unread messages for the current user
        queryset = self.get_queryset()

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
        # Filter messages to only include unread messages received by the user
        return Message.objects.filter(receiver=self.request.user, is_read=False)


class SentMessagesListView(generics.ListAPIView):
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


class ReceivedMessagesListView(generics.ListAPIView):
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
