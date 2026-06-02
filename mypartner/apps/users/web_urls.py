from django.urls import path
from . import web_views

urlpatterns = [
    path('', lambda req: __import__('django.shortcuts', fromlist=['redirect']).redirect('main-menu'), name='home'),
    path('login/', web_views.login_view, name='login'),
    path('logout/', web_views.logout_view, name='logout'),
    path('register/', web_views.register_view, name='register'),
    path('password-recovery/', web_views.password_recovery_view, name='password-recovery'),
    path('password-recovery/confirm/', web_views.password_recovery_confirm_view, name='password-recovery-confirm'),
    path('verify-email/', web_views.verify_email_view, name='verify-email'),
    path('menu/', web_views.menu_view, name='main-menu'),
    path('settings/', web_views.settings_view, name='user-settings'),
]
