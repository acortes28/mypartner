from django.urls import path
from . import views

urlpatterns = [
    # ── Grupo-scoped ──────────────────────────────────────────────────────
    path('groups/<uuid:group_id>/finances/dashboard/', views.FinanciasDashboardView.as_view(), name='api-finances-dashboard'),
    path('groups/<uuid:group_id>/concepts/', views.ConceptoListCreateView.as_view(), name='api-concept-list-create'),
    path('groups/<uuid:group_id>/concepts/<uuid:concept_id>/', views.ConceptoDetailView.as_view(), name='api-concept-detail'),
    path('groups/<uuid:group_id>/concepts/<uuid:concept_id>/delete-with-movements/', views.ConceptoDeleteWithMovementsView.as_view(), name='api-concept-delete-with-movements'),
    path('groups/<uuid:group_id>/movements/', views.MovimientoListView.as_view(), name='api-movement-list'),
    path('groups/<uuid:group_id>/movements/export/', views.MovimientoExportView.as_view(), name='api-movement-export'),
    path('groups/<uuid:group_id>/movements/<uuid:movement_id>/', views.MovimientoDetailView.as_view(), name='api-movement-detail'),
    path('groups/<uuid:group_id>/budget/', views.PresupuestoListCreateView.as_view(), name='api-budget-list-create'),
    path('groups/<uuid:group_id>/budget/<uuid:budget_id>/', views.PresupuestoDetailView.as_view(), name='api-budget-detail'),
    # Ahorros grupales
    path('groups/<uuid:group_id>/savings/', views.MetaAhorroGrupalListCreateView.as_view(), name='api-savings-group-list-create'),
    path('groups/<uuid:group_id>/savings/<uuid:meta_id>/', views.MetaAhorroGrupalDetailView.as_view(), name='api-savings-group-detail'),
    path('groups/<uuid:group_id>/savings/<uuid:meta_id>/aportar/', views.MetaAhorroGrupalAportarView.as_view(), name='api-savings-group-aportar'),
    path('groups/<uuid:group_id>/savings/<uuid:meta_id>/archivar/', views.MetaAhorroGrupalArchivarView.as_view(), name='api-savings-group-archivar'),

    # ── Personal ──────────────────────────────────────────────────────────
    path('personal/dashboard/', views.FinanciasDashboardPersonalView.as_view(), name='api-personal-dashboard'),
    # Conceptos personales
    path('personal/concepts/', views.ConceptoPersonalListCreateView.as_view(), name='api-personal-concept-list-create'),
    path('personal/concepts/<uuid:concept_id>/', views.ConceptoPersonalDetailView.as_view(), name='api-personal-concept-detail'),
    path('personal/concepts/<uuid:concept_id>/delete-with-movements/', views.ConceptoPersonalDeleteWithMovementsView.as_view(), name='api-personal-concept-delete-with-movements'),
    # Movimientos personales
    path('personal/movements/', views.MovimientoPersonalListView.as_view(), name='api-personal-movement-list'),
    path('personal/movements/<uuid:movement_id>/', views.MovimientoPersonalDetailView.as_view(), name='api-personal-movement-detail'),
    path('personal/movements/<uuid:movement_id>/replicate/', views.ReplicarMovimientoView.as_view(), name='api-movement-replicate'),
    path('personal/movements/<uuid:movement_id>/correct/', views.MovimientoPersonalCorrectView.as_view(), name='api-personal-movement-correct'),
    # Presupuesto personal
    path('personal/budget/', views.PresupuestoPersonalListCreateView.as_view(), name='api-personal-budget-list-create'),
    path('personal/budget/<uuid:budget_id>/', views.PresupuestoPersonalDetailView.as_view(), name='api-personal-budget-detail'),
    # Gastos compartidos
    path('personal/shared/', views.GastoCompartidoListView.as_view(), name='api-shared-list'),
    path('personal/shared/<uuid:gasto_id>/pay/', views.MarcarGastoPagadoView.as_view(), name='api-shared-pay'),
    path('personal/shared/liquidar/', views.LiquidarView.as_view(), name='api-shared-liquidar'),
    # Asistente de división
    path('personal/split/confirm/', views.SplitConfirmView.as_view(), name='api-split-confirm'),
    # Ahorros personales
    path('personal/savings/', views.MetaAhorroPersonalListCreateView.as_view(), name='api-personal-savings-list-create'),
    path('personal/savings/<uuid:meta_id>/', views.MetaAhorroPersonalDetailView.as_view(), name='api-personal-savings-detail'),
    path('personal/savings/<uuid:meta_id>/aportar/', views.MetaAhorroPersonalAportarView.as_view(), name='api-personal-savings-aportar'),
    path('personal/savings/<uuid:meta_id>/retirar/', views.MetaAhorroPersonalRetirarView.as_view(), name='api-personal-savings-retirar'),
    path('personal/savings/<uuid:meta_id>/archivar/', views.MetaAhorroPersonalArchivarView.as_view(), name='api-personal-savings-archivar'),
    # Tarjetas
    path('personal/cards/', views.TarjetaListCreateView.as_view(), name='api-personal-cards-list-create'),
    path('personal/cards/<uuid:card_id>/', views.TarjetaDetailView.as_view(), name='api-personal-cards-detail'),
]
