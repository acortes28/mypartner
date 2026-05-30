import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import User, PasswordResetToken


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main-menu')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'main-menu'))
        messages.error(request, 'Usuario o contraseña inválidos.')
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('main-menu')
    if request.method == 'POST':
        data = {k: request.POST.get(k, '').strip() for k in
                ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']}

        errors = {}
        if User.objects.filter(username=data['username']).exists():
            errors['username'] = 'Este nombre de usuario ya está en uso.'
        if User.objects.filter(email=data['email']).exists():
            errors['email'] = 'Este correo ya está en uso.'
        if data['password'] != data['confirm_password']:
            errors['confirm_password'] = 'Las contraseñas no coinciden.'

        if not errors:
            temp_user = User(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
            )
            try:
                validate_password(data['password'], user=temp_user)
            except ValidationError as e:
                errors['password'] = list(e.messages)

        if errors:
            return render(request, 'users/register.html', {'errors': errors, 'form_data': data})

        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            password=data['password'],
        )
        messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'users/register.html')


def password_recovery_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, 'users/password_recovery.html', {
                'email_not_found': True,
                'email_value': email,
            })

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expira_en=timezone.now() + timedelta(minutes=10),
        )

        # Usar FRONTEND_URL para que el link funcione tanto en local como en Docker
        recovery_url = f"{settings.FRONTEND_URL.rstrip('/')}/password-recovery/confirm/?token={raw_token}"

        try:
            html_body = render_to_string('emails/password_recovery.html', {'recovery_url': recovery_url})
            msg = EmailMultiAlternatives(
                subject='Recupera tu contraseña — Finanzosos',
                body=f'Haz clic aquí para cambiar tu contraseña:\n\n{recovery_url}\n\nEste enlace expira en 10 minutos.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send(fail_silently=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Error al enviar correo de recuperación a %s', email)
            messages.error(request, f'Error al enviar el correo: {e}')
            return redirect('password-recovery')

        messages.success(request, 'Si el correo está registrado, recibirás un enlace de recuperación.')
        return redirect('password-recovery')
    return render(request, 'users/password_recovery.html')


def password_recovery_confirm_view(request):
    token = request.GET.get('token') or request.POST.get('token', '')
    token_hash = hashlib.sha256(token.encode()).hexdigest() if token else ''

    try:
        reset_token = PasswordResetToken.objects.select_related('user').get(
            token_hash=token_hash, usado=False
        )
        if timezone.now() > reset_token.expira_en:
            messages.error(request, 'El enlace de recuperación ha expirado.')
            return redirect('password-recovery')
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'El enlace de recuperación es inválido o ya fue utilizado.')
        return redirect('password-recovery')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        if password != confirm:
            return render(request, 'users/password_recovery_confirm.html',
                          {'token': token, 'error': 'Las contraseñas no coinciden.'})
        try:
            validate_password(password, user=reset_token.user)
        except ValidationError as e:
            return render(request, 'users/password_recovery_confirm.html',
                          {'token': token, 'error': ' '.join(e.messages)})
        reset_token.user.set_password(password)
        reset_token.user.save()
        reset_token.usado = True
        reset_token.save()
        messages.success(request, 'Contraseña cambiada exitosamente. Ya puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'users/password_recovery_confirm.html', {'token': token})


@login_required
def menu_view(request):
    return render(request, 'users/menu.html')


@login_required
def settings_view(request):
    return render(request, 'users/settings.html')
