from django.urls import path
from . import web_views

urlpatterns = [
    path('announcements/', web_views.announcements_select_view, name='announcements-index'),
    path('announcements/groups/<uuid:group_id>/', web_views.announcements_view, name='announcements-group'),
    path('announcements/groups/<uuid:group_id>/<uuid:announcement_id>/', web_views.announcement_detail_view, name='announcement-detail'),
]
