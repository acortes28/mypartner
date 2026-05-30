import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, PasswordResetToken
from .serializers import (
    LoginSerializer,
    PasswordRecoveryConfirmSerializer,
    PasswordRecoveryRequestSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Registro exitoso. Ya puedes iniciar sesión.'},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        })


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Sesión cerrada exitosamente.'})


class UserProfileView(APIView):
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class PasswordRecoveryRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordRecoveryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Always return success to avoid email enumeration
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Te enviamos un correo con el link de recuperación.'})

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expira_en = timezone.now() + timedelta(minutes=10)

        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expira_en=expira_en,
        )

        recovery_url = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        send_mail(
            subject='Recupera tu contraseña — Finanzosos',
            message=f'Haz clic en el siguiente enlace para cambiar tu contraseña:\n\n{recovery_url}\n\nEste enlace expira en 10 minutos.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

        return Response({'detail': 'Te enviamos un correo con el link de recuperación.'})


class PasswordRecoveryConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordRecoveryConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_token = serializer.validated_data['token']
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            reset_token = PasswordResetToken.objects.select_related('user').get(
                token_hash=token_hash, usado=False
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'detail': 'El enlace de recuperación es inválido o ya fue utilizado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > reset_token.expira_en:
            return Response(
                {'detail': 'El enlace de recuperación ha expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_token.user
        password = serializer.validated_data['password']

        try:
            validate_password(password, user=user)
        except DjangoValidationError as e:
            return Response(
                {'password': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save()
        reset_token.usado = True
        reset_token.save()

        return Response({'detail': 'Contraseña cambiada exitosamente.'})
