from django.urls import path
from . import web_views

urlpatterns = [
    path('announcements/', web_views.announcements_view, name='announcements-index'),
    path('announcements/<uuid:announcement_id>/', web_views.announcement_detail_view, name='announcement-detail'),
]
