from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PasswordResetToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'expira_en', 'usado', 'created_at']
    list_filter = ['usado']
    readonly_fields = ['token_hash', 'created_at']
