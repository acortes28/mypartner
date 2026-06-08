from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'confirm_password']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Este nombre de usuario ya está en uso.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este correo ya está en uso.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Las contraseñas no coinciden.'})

        user = User(
            username=attrs.get('username', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    grupo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'grupo_nombre']
        read_only_fields = fields

    def get_grupo_nombre(self, obj):
        membership = obj.memberships.select_related('grupo').filter(grupo__activo=True).first()
        if membership:
            return membership.grupo.nombre
        return 'Sin grupo'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate as _auth
        user = _auth(username=attrs['username'], password=attrs['password'])
        if not user:
            # Check if user exists but is inactive (unverified email)
            from .models import User as _User
            try:
                existing = _User.objects.get(username=attrs['username'])
                existing.check_password(attrs['password'])
                if not existing.is_active:
                    raise serializers.ValidationError(
                        'Debes verificar tu correo electrónico antes de iniciar sesión.'
                    )
            except _User.DoesNotExist:
                pass
            raise serializers.ValidationError('Usuario o contraseña inválidos.')
        attrs['user'] = user
        return attrs


class PasswordRecoveryRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordRecoveryConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Las contraseñas no coinciden.'})
        return attrs
