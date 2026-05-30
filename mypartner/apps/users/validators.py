import re
from django.core.exceptions import ValidationError


class HasUppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                'La contraseña debe contener al menos una letra mayúscula.',
                code='password_no_upper',
            )

    def get_help_text(self):
        return 'Al menos una letra mayúscula.'


class HasLowercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                'La contraseña debe contener al menos una letra minúscula.',
                code='password_no_lower',
            )

    def get_help_text(self):
        return 'Al menos una letra minúscula.'


class HasDigitValidator:
    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                'La contraseña debe contener al menos un número.',
                code='password_no_digit',
            )

    def get_help_text(self):
        return 'Al menos un número.'


class HasSpecialCharValidator:
    SPECIAL_CHARS = r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>/?\\`~]'

    def validate(self, password, user=None):
        if not re.search(self.SPECIAL_CHARS, password):
            raise ValidationError(
                'La contraseña debe contener al menos un carácter especial.',
                code='password_no_special',
            )

    def get_help_text(self):
        return 'Al menos un carácter especial (!@#$%^&*...).'


class NotContainsUserInfoValidator:
    def validate(self, password, user=None):
        if user is None:
            return
        pwd_lower = password.lower()
        checks = [
            (getattr(user, 'username', ''), 'nombre de usuario'),
            (getattr(user, 'first_name', ''), 'nombre'),
            (getattr(user, 'last_name', ''), 'apellido'),
        ]
        for value, label in checks:
            if value and len(value) >= 3 and value.lower() in pwd_lower:
                raise ValidationError(
                    f'La contraseña no puede contener el {label}.',
                    code='password_contains_user_info',
                )

    def get_help_text(self):
        return 'No debe contener tu nombre de usuario, nombre ni apellido.'
