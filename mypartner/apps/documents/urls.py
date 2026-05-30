from django.urls import path
from . import views

urlpatterns = [
    path('groups/<uuid:group_id>/documents/', views.DocumentoListCreateView.as_view(), name='document-list-create'),
    path('groups/<uuid:group_id>/documents/<uuid:document_id>/', views.DocumentoDeleteView.as_view(), name='document-delete'),
]
