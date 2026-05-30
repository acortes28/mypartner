from django.urls import path
from . import web_views

urlpatterns = [
    path('notifications/', web_views.notifications_view, name='notifications-index'),
    path('notifications/stream/', web_views.sse_notifications_view, name='notifications-stream'),
    path('notifications/unread/', web_views.notifications_unread_json_view, name='notifications-unread-json'),
    path('notifications/<uuid:notification_id>/read/', web_views.mark_read_view, name='notification-read'),
    path('notifications/read-all/', web_views.mark_all_read_view, name='notifications-read-all'),
]
