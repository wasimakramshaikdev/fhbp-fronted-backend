import logging
from django.core.cache import cache
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from apps.core.responses import api_response
from apps.core.services.audit import AuditService
from apps.accounts.models import User, PasswordResetToken, EmailVerificationToken
from apps.accounts.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer
)
from apps.accounts.authentication import JWTTokenService

logger = logging.getLogger(__name__)

def check_rate_limit(request, action_key: str, max_attempts: int = 5, window_seconds: int = 60) -> bool:
    """Helper to enforce Redis-backed rate limiting per client IP."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
    cache_key = f"ratelimit:{action_key}:{ip}"
    attempts = cache.get(cache_key, 0)
    if attempts >= max_attempts:
        return False
    cache.set(cache_key, attempts + 1, timeout=window_seconds)
    return True


class RegisterView(APIView):
    """
    Public registration endpoint for Customers and Hall Owners.
    Automatically provisions OwnerProfile for owners.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not check_rate_limit(request, 'register', max_attempts=10, window_seconds=300):
            return api_response(
                message="Too many registration attempts. Please try again in a few minutes.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                success=False,
                code="RATE_LIMIT_EXCEEDED"
            )

        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Registration validation failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="VALIDATION_ERROR"
            )

        user = serializer.save()
        tokens = JWTTokenService.generate_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        AuditService.log_action(
            actor=user,
            action="USER_REGISTERED",
            obj=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            changes={"email": user.email, "role": user.role}
        )

        response = api_response(
            data={
                "user": user_data,
                "tokens": tokens,
                "access_token": tokens['access_token'],
                "refresh_token": tokens['refresh_token'],
                "expires_in": tokens['expires_in'],
            },
            message="Account registered successfully.",
            status_code=status.HTTP_201_CREATED
        )

        # Set secure HttpOnly refresh cookie
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh_token'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60  # 7 days
        )

        return response


class LoginView(APIView):
    """
    Email & password authentication returning JWT access token and setting HttpOnly refresh cookie.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not check_rate_limit(request, 'login', max_attempts=8, window_seconds=60):
            return api_response(
                message="Too many login attempts. Please wait 60 seconds before trying again.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                success=False,
                code="RATE_LIMIT_EXCEEDED"
            )

        serializer = UserLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Invalid email or password.",
                errors=serializer.errors,
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                code="AUTHENTICATION_FAILED"
            )

        user = serializer.validated_data['user']
        tokens = JWTTokenService.generate_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        AuditService.log_action(
            actor=user,
            action="USER_LOGGED_IN",
            obj=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        response = api_response(
            data={
                "user": user_data,
                "tokens": tokens,
                "access_token": tokens['access_token'],
                "refresh_token": tokens['refresh_token'],
                "expires_in": tokens['expires_in'],
            },
            message="Logged in successfully."
        )

        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh_token'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60
        )

        return response


class RefreshTokenView(APIView):
    """
    Rotates refresh token and returns a new Access Token.
    Accepts token from HttpOnly cookie or request payload.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        from apps.accounts.authentication import extract_refresh_token_from_cookies
        refresh_token = (
            request.data.get('refresh_token')
            or extract_refresh_token_from_cookies(request.COOKIES)
            or request.COOKIES.get('refresh_token')
        )
        if not refresh_token:
            return api_response(
                message="Refresh token is required.",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="MISSING_TOKEN"
            )

        try:
            payload = JWTTokenService.decode_token(refresh_token, expected_type='refresh')
            user_id = payload.get('user_id') or payload.get('sub') or payload.get('id')
            email = payload.get('email') or payload.get('user_email')

            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id, is_active=True)
                except (User.DoesNotExist, ValueError):
                    pass

            if not user and email:
                try:
                    user = User.objects.get(email=email, is_active=True)
                except User.DoesNotExist:
                    pass

            if not user:
                raise AuthenticationFailed('User not found or deactivated.')

            # Invalidate old refresh token
            JWTTokenService.revoke_refresh_token(refresh_token, user)

            # Generate new token pair
            new_tokens = JWTTokenService.generate_tokens_for_user(user)

            response = api_response(
                data={
                    "access_token": new_tokens['access_token'],
                    "refresh_token": new_tokens['refresh_token'],
                    "tokens": new_tokens,
                    "expires_in": new_tokens['expires_in'],
                },
                message="Token refreshed successfully."
            )

            response.set_cookie(
                key='refresh_token',
                value=new_tokens['refresh_token'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                max_age=7 * 24 * 60 * 60
            )

            return response
        except Exception as exc:
            return api_response(
                message="Invalid or expired refresh token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                success=False,
                code="INVALID_REFRESH_TOKEN"
            )


class LogoutView(APIView):
    """
    Revokes the active refresh token and clears session cookies.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh_token')
        if refresh_token:
            JWTTokenService.revoke_refresh_token(refresh_token, request.user)

        AuditService.log_action(
            actor=request.user,
            action="USER_LOGGED_OUT",
            obj=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        response = api_response(message="Logged out successfully.")
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response


class CurrentUserView(APIView):
    """
    Retrieves or updates current authenticated user profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return api_response(data=serializer.data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Profile update validation failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="VALIDATION_ERROR"
            )

        updated_user = serializer.update(request.user, serializer.validated_data)
        return api_response(
            data=UserProfileSerializer(updated_user).data,
            message="Profile updated successfully."
        )


class PasswordResetRequestView(APIView):
    """
    Initiates password recovery by issuing a single-use secure reset token.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Invalid email address.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email, is_active=True).first()

        # Always return success to prevent user email enumeration
        if user:
            reset_token = PasswordResetToken.create_for_user(user)
            logger.info(f"Password reset token for {user.email}: {reset_token.token}")

        return api_response(
            message="If an account with this email exists, a password reset link has been sent."
        )


class PasswordResetConfirmView(APIView):
    """
    Completes password reset using verified single-use token.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Password reset validation failed.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="VALIDATION_ERROR"
            )

        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            token_obj = PasswordResetToken.objects.get(token=token_str)
            if not token_obj.is_valid:
                return api_response(
                    message="Password reset token has expired or has already been used.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    success=False,
                    code="TOKEN_EXPIRED"
                )

            user = token_obj.user
            user.set_password(new_password)
            user.save()

            token_obj.is_used = True
            token_obj.save()

            AuditService.log_action(
                actor=user,
                action="PASSWORD_RESET_COMPLETED",
                obj=user,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            return api_response(message="Password reset successfully. You may now sign in with your new password.")
        except PasswordResetToken.DoesNotExist:
            return api_response(
                message="Invalid password reset token.",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="INVALID_TOKEN"
            )


class VerifyEmailView(APIView):
    """
    Verifies user email address using single-use email verification token.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(
                message="Token is required.",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False
            )

        token_str = serializer.validated_data['token']
        try:
            token_obj = EmailVerificationToken.objects.get(token=token_str)
            if not token_obj.is_valid:
                return api_response(
                    message="Email verification token has expired or already used.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    success=False,
                    code="TOKEN_EXPIRED"
                )

            user = token_obj.user
            user.is_verified = True
            user.save()

            token_obj.is_used = True
            token_obj.save()

            return api_response(message="Email verified successfully.")
        except EmailVerificationToken.DoesNotExist:
            return api_response(
                message="Invalid verification token.",
                status_code=status.HTTP_400_BAD_REQUEST,
                success=False,
                code="INVALID_TOKEN"
            )
