from rest_framework import serializers
from .models import Meeting, MeetingParticipant, MeetingMessage, MeetingRecording
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar']


class MeetingParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MeetingParticipant
        fields = ['user', 'joined_at', 'is_audio_enabled', 'is_video_enabled', 'is_screen_sharing']


class MeetingMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = MeetingMessage
        fields = ['id', 'sender', 'content', 'message_type', 'timestamp']


class MeetingRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRecording
        fields = ['id', 'file', 'duration', 'created_at']


class MeetingSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    meeting_participants = MeetingParticipantSerializer(many=True, read_only=True)
    messages = MeetingMessageSerializer(many=True, read_only=True)
    recordings = MeetingRecordingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'description', 'host', 'participants', 'meeting_participants',
            'scheduled_time', 'duration', 'status', 'is_public', 'password',
            'created_at', 'updated_at', 'ended_at', 'messages', 'recordings'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ended_at']



