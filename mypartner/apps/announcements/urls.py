from django.urls import path
from . import views

urlpatterns = [
    path('groups/<uuid:group_id>/announcements/', views.AnuncioListCreateView.as_view(), name='announcement-list-create'),
    path('groups/<uuid:group_id>/announcements/<uuid:announcement_id>/', views.AnuncioDetailDeleteView.as_view(), name='announcement-detail'),
    path('groups/<uuid:group_id>/announcements/<uuid:announcement_id>/comments/', views.ComentarioCreateView.as_view(), name='comment-create'),
]
