from django.urls import path
from . import views

urlpatterns = [
    path('groups/my-group/', views.MyGroupView.as_view(), name='my-group'),
    path('groups/', views.CreateGroupView.as_view(), name='create-group'),
    path('groups/<uuid:group_id>/', views.DeleteGroupView.as_view(), name='delete-group'),
    path('groups/<uuid:group_id>/invite/', views.InviteMemberView.as_view(), name='invite-member'),
    path('groups/<uuid:group_id>/remove-member/', views.RemoveMemberView.as_view(), name='remove-member'),
    path('groups/<uuid:group_id>/set-role/', views.SetRoleView.as_view(), name='set-role'),
    path('groups/<uuid:group_id>/leave/', views.LeaveGroupView.as_view(), name='leave-group'),
    path('invitations/', views.InvitationListView.as_view(), name='invitation-list'),
    path('invitations/<uuid:invitation_id>/accept/', views.AcceptInvitationView.as_view(), name='accept-invitation'),
    path('invitations/<uuid:invitation_id>/reject/', views.RejectInvitationView.as_view(), name='reject-invitation'),
]
