from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.NotificacionListView.as_view(), name='notification-list'),
    path('notifications/<uuid:notification_id>/read/', views.MarkNotificacionReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', views.MarkAllNotificacionesReadView.as_view(), name='notification-read-all'),
]
