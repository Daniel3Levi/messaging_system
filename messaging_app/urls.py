from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationViewSet, UserLoginViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView)
from .views import (ReceivedMessagesViewSet, DeleteMessageViewSet, SentMessagesViewSet,
                    CreateMessageViewSet, ReadMessageViewSet, UnreadMessageViewSet)

# Users
auth_router = DefaultRouter()
#
auth_router.register(r'register', UserRegistrationViewSet, basename='register')
auth_router.register(r'login', UserLoginViewSet, basename='login')

# # Messages
message_router = DefaultRouter()
message_router.register(r'create', CreateMessageViewSet, basename='create')
message_router.register(r'read', ReadMessageViewSet, basename='read')
message_router.register(r'delete', DeleteMessageViewSet, basename='delete')
message_router.register(r'received', ReceivedMessagesViewSet, basename='received')
message_router.register(r'sent', SentMessagesViewSet, basename='sent')
message_router.register(r'unread', UnreadMessageViewSet, basename='unread')

urlpatterns = [
    path('auth/', include(auth_router.urls)),
    path('', include(message_router.urls)),
    # JWT Token
    path('jwt/create/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('jwt/verify/', TokenVerifyView.as_view(), name='token-verify'),
]
