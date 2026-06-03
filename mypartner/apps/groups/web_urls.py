from django.urls import path
from . import web_views

urlpatterns = [
    path('groups/manage/', web_views.group_manage_view, name='group-manage'),
    path('groups/manage/<uuid:group_id>/', web_views.group_manage_detail_view, name='group-manage-detail'),
    path('invitations/<uuid:invitation_id>/', web_views.invitation_view, name='invitation-detail'),
]
