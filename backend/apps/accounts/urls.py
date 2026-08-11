from django.urls import path
from apps.accounts.views import (
    RegisterView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    CurrentUserView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    VerifyEmailView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshTokenView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', CurrentUserView.as_view(), name='auth-me'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='auth-password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
]
