from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/password-recovery/', views.PasswordRecoveryRequestView.as_view(), name='password-recovery-request'),
    path('auth/password-recovery/confirm/', views.PasswordRecoveryConfirmView.as_view(), name='password-recovery-confirm'),
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
]
