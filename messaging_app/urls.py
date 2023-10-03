from django.urls import path
from .views import (MessageCreateView, MessageDetailView, UnreadMessageListView,
                    SentMessagesListView, ReceivedMessagesListView)
from .views import UserRegistrationView, UserLoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView)

urlpatterns = [
    # User
    path("auth/register/", UserRegistrationView.as_view(), name="user-register"),
    path("auth/login/", UserLoginView.as_view(), name="user-login"),
    # JWT Token
    path('auth/jwt/create/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/jwt/verify/', TokenVerifyView.as_view(), name='token-verify'),
    # Messages
    path("new-message/", MessageCreateView.as_view(), name="create-new-message"),
    path("read-message/<int:pk>/", MessageDetailView.as_view(), name="read-message"),
    path("unread-messages/", UnreadMessageListView.as_view(), name="unread-messages"),
    path("sent-messages/", SentMessagesListView.as_view(), name="sent-messages"),
    path("received-messages/", ReceivedMessagesListView.as_view(), name="received-messages"),
]
