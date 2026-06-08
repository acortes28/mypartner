import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, PasswordResetToken, EmailVerificationToken
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
        user = serializer.save()

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expira_en = timezone.now() + timedelta(hours=24)

        EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expira_en=expira_en,
        )

        verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email/?token={raw_token}"
        try:
            html_body = render_to_string('emails/email_verification.html', {
                'verify_url': verify_url,
                'first_name': user.first_name,
            })
            msg = EmailMultiAlternatives(
                subject='Verifica tu correo — Finanzosos',
                body=f'Haz clic en el siguiente enlace para verificar tu correo:\n\n{verify_url}\n\nEste enlace expira en 24 horas.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Error al enviar correo de verificación a %s', user.email)

        return Response(
            {'detail': 'Registro exitoso. Revisa tu correo para verificar tu cuenta.'},
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

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'No existe una cuenta registrada con ese correo electrónico.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expira_en = timezone.now() + timedelta(minutes=10)

        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expira_en=expira_en,
        )

        recovery_url = f"{settings.FRONTEND_URL.rstrip('/')}/password-recovery/confirm/?token={raw_token}"
        try:
            html_body = render_to_string('emails/password_recovery.html', {'recovery_url': recovery_url})
            msg = EmailMultiAlternatives(
                subject='Recupera tu contraseña — Finanzosos',
                body=f'Haz clic en el siguiente enlace para cambiar tu contraseña:\n\n{recovery_url}\n\nEste enlace expira en 10 minutos.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Error al enviar correo de recuperación (API) a %s', email)

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


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        raw_token = request.query_params.get('token', '')
        if not raw_token:
            return Response(
                {'detail': 'Token requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            verification = EmailVerificationToken.objects.select_related('user').get(
                token_hash=token_hash, usado=False
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {'detail': 'El enlace de verificación es inválido o ya fue utilizado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > verification.expira_en:
            return Response(
                {'detail': 'El enlace de verificación ha expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = verification.user
        user.is_active = True
        user.save(update_fields=['is_active'])
        verification.usado = True
        verification.save(update_fields=['usado'])

        return Response({'detail': 'Correo verificado exitosamente. Ya puedes iniciar sesión.'})
