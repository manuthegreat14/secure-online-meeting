from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from meetings.models import Meeting, MeetingParticipant
from meetings.serializers import MeetingSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class MeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Meeting.objects.filter(
            participants=self.request.user
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        meeting = self.get_object()
        if request.user not in meeting.participants.all():
            meeting.participants.add(request.user)
            return Response({'status': 'joined'})
        return Response({'status': 'already_joined'})
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        meeting = self.get_object()
        if request.user in meeting.participants.all():
            meeting.participants.remove(request.user)
            return Response({'status': 'left'})
        return Response({'status': 'not_participant'})
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        meeting = self.get_object()
        if meeting.host == request.user and meeting.status == 'scheduled':
            meeting.start_meeting()
            return Response({'status': 'started'})
        return Response({'status': 'cannot_start'})
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        meeting = self.get_object()
        if meeting.host == request.user and meeting.status == 'active':
            meeting.end_meeting()
            return Response({'status': 'ended'})
        return Response({'status': 'cannot_end'})



