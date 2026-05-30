from django.urls import path
from . import views

urlpatterns = [
    path('groups/<uuid:group_id>/finances/dashboard/', views.FinanciasDashboardView.as_view(), name='finances-dashboard'),
    path('groups/<uuid:group_id>/concepts/', views.ConceptoListCreateView.as_view(), name='concept-list-create'),
    path('groups/<uuid:group_id>/concepts/<uuid:concept_id>/', views.ConceptoDetailView.as_view(), name='concept-detail'),
    path('groups/<uuid:group_id>/concepts/<uuid:concept_id>/delete-with-movements/', views.ConceptoDeleteWithMovementsView.as_view(), name='concept-delete-with-movements'),
    path('groups/<uuid:group_id>/movements/', views.MovimientoListCreateView.as_view(), name='movement-list-create'),
    path('groups/<uuid:group_id>/movements/export/', views.MovimientoExportView.as_view(), name='movement-export'),
    path('groups/<uuid:group_id>/movements/<uuid:movement_id>/', views.MovimientoDetailView.as_view(), name='movement-detail'),
    path('groups/<uuid:group_id>/budget/', views.PresupuestoListCreateView.as_view(), name='budget-list-create'),
    path('groups/<uuid:group_id>/budget/<uuid:budget_id>/', views.PresupuestoDetailView.as_view(), name='budget-detail'),
]
