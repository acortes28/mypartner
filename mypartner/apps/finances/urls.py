from django.urls import path
from . import views

urlpatterns = [
    # Grupo-scoped
    path('groups/<uuid:group_id>/finances/dashboard/', views.FinanciasDashboardView.as_view(), name='api-finances-dashboard'),
    path('groups/<uuid:group_id>/concepts/', views.ConceptoListCreateView.as_view(), name='api-concept-list-create'),
    path('groups/<uuid:group_id>/concepts/<uuid:concept_id>/', views.ConceptoDetailView.as_view(), name='api-concept-detail'),
    path('groups/<uuid:group_id>/concepts/<uuid:concept_id>/delete-with-movements/', views.ConceptoDeleteWithMovementsView.as_view(), name='api-concept-delete-with-movements'),
    path('groups/<uuid:group_id>/movements/', views.MovimientoListView.as_view(), name='api-movement-list'),
    path('groups/<uuid:group_id>/movements/export/', views.MovimientoExportView.as_view(), name='api-movement-export'),
    path('groups/<uuid:group_id>/movements/<uuid:movement_id>/', views.MovimientoDetailView.as_view(), name='api-movement-detail'),
    path('groups/<uuid:group_id>/budget/', views.PresupuestoListCreateView.as_view(), name='api-budget-list-create'),
    path('groups/<uuid:group_id>/budget/<uuid:budget_id>/', views.PresupuestoDetailView.as_view(), name='api-budget-detail'),
    # Personal
    path('personal/dashboard/', views.FinanciasDashboardPersonalView.as_view(), name='api-personal-dashboard'),
    path('personal/movements/', views.MovimientoPersonalListView.as_view(), name='api-personal-movement-list'),
    path('personal/movements/<uuid:movement_id>/', views.MovimientoPersonalDetailView.as_view(), name='api-personal-movement-detail'),
    path('personal/movements/<uuid:movement_id>/replicate/', views.ReplicarMovimientoView.as_view(), name='api-movement-replicate'),
]
