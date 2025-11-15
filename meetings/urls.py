from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    path('', views.MeetingListView.as_view(), name='meeting_list'),
    path('create/', views.MeetingCreateView.as_view(), name='meeting_create'),
    path('<uuid:pk>/', views.meeting_detail, name='meeting_detail'),
    path('<uuid:pk>/update/', views.MeetingUpdateView.as_view(), name='meeting_update'),
    path('<uuid:pk>/delete/', views.MeetingDeleteView.as_view(), name='meeting_delete'),
    path('join/', views.join_meeting, name='join_meeting'),
    # path('join/<uuid:meeting_id>/', views.join_meeting_direct, name='join_meeting_direct'),
    path('<uuid:pk>/lobby/', views.lobby, name='lobby'),
    path('<uuid:pk>/verify/', views.verify_and_enter, name='verify_and_enter'),
    path('verify-face/', views.verify_face, name='verify_face'),
    path('<uuid:pk>/room/', views.meeting_room, name='meeting_room'),
    path('<uuid:pk>/start/', views.start_meeting, name='start_meeting'),
    path('<uuid:pk>/end/', views.end_meeting, name='end_meeting'),
    path('<uuid:pk>/leave/', views.leave_meeting, name='leave_meeting'),
    path('<uuid:pk>/participants/', views.get_meeting_participants, name='get_meeting_participants'),
    path('<uuid:pk>/messages/', views.get_meeting_messages, name='get_meeting_messages'),
]



