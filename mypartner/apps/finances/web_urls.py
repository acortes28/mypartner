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
]
