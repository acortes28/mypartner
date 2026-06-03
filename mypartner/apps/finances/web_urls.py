from django.urls import path
from . import web_views

urlpatterns = [
    path('finances/', web_views.dashboard_view, name='finances-dashboard'),
    path('finances/budget/', web_views.budget_view, name='finances-budget'),
    path('finances/concepts/', web_views.concepts_view, name='finances-concepts'),
    path('finances/movements/', web_views.movements_view, name='finances-movements'),
    path('finances/movements/<uuid:movement_id>/', web_views.movement_detail_view, name='finances-movement-detail'),
    path('finances/export/', web_views.export_csv_view, name='finances-export'),
    path('finances/add-movement/', web_views.add_movement_view, name='finances-add-movement'),
    path('finances/shared/', web_views.gastos_compartidos_view, name='finances-shared'),
    path('finances/split/', web_views.split_assistant_view, name='finances-split'),
    path('finances/split/confirm/', web_views.split_confirm_view, name='finances-split-confirm'),
    path('finances/groups/', web_views.group_finances_list_view, name='finances-group-list'),
    path('finances/groups/<uuid:group_id>/', web_views.group_finances_view, name='finances-group'),
    # Ahorros
    path('finances/savings/', web_views.savings_personal_view, name='finances-savings-personal'),
    path('finances/savings/<uuid:meta_id>/', web_views.savings_personal_detail_view, name='finances-savings-personal-detail'),
    path('finances/groups/<uuid:group_id>/savings/', web_views.savings_group_view, name='finances-savings-group'),
    path('finances/groups/<uuid:group_id>/savings/<uuid:meta_id>/', web_views.savings_group_detail_view, name='finances-savings-group-detail'),
]
