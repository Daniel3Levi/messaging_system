from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from messaging_app.views import UserRegistrationViewSet, UserLoginViewSet
from messaging_app.views import (NewMessageViewSet, ReadMessageViewSet, UnreadMessagesViewSet,
                                 SentMessagesViewSet, ReceivedMessagesViewSet)

# Users
auth_router = DefaultRouter()
#
auth_router.register(r'register', UserRegistrationViewSet, basename='register')
auth_router.register(r'login', UserLoginViewSet, basename='login')

# Messages
message_router = DefaultRouter()
#
message_router.register(r'new-message', NewMessageViewSet, basename='new-message')
message_router.register(r'read-message', ReadMessageViewSet, basename='read-message')
message_router.register(r'unread-messages', UnreadMessagesViewSet, basename='unread-messages')
message_router.register(r'sent-messages', SentMessagesViewSet, basename='sent-messages')
message_router.register(r'received-messages', ReceivedMessagesViewSet, basename='received-messages')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(message_router.urls)),
    path('api/v1/auth/', include(auth_router.urls)),
    # Just for JWT
    path('api/v1/auth/', include('messaging_app.urls'))


]
