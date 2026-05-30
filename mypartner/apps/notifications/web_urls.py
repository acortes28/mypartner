from django.urls import path
from . import web_views

urlpatterns = [
    path('notifications/', web_views.notifications_view, name='notifications-index'),
    path('notifications/<uuid:notification_id>/read/', web_views.mark_read_view, name='notification-read'),
    path('notifications/read-all/', web_views.mark_all_read_view, name='notifications-read-all'),
]
