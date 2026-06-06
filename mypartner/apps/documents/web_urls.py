from django.urls import path
from . import web_views

urlpatterns = [
    path('documents/', web_views.documents_select_view, name='documents-index'),
    path('documents/groups/<uuid:group_id>/', web_views.documents_view, name='documents-group'),
]
