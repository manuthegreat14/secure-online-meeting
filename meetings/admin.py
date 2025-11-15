from django.contrib import admin
from .models import Meeting, MeetingParticipant, MeetingMessage, MeetingRecording


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'status', 'scheduled_time', 'is_public', 'created_at')
    list_filter = ('status', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'host__username', 'host__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'ended_at')
    filter_horizontal = ('participants',)


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'meeting', 'joined_at', 'is_audio_enabled', 'is_video_enabled')
    list_filter = ('is_audio_enabled', 'is_video_enabled', 'is_screen_sharing', 'joined_at')
    search_fields = ('user__username', 'user__email', 'meeting__title')


@admin.register(MeetingMessage)
class MeetingMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'meeting', 'message_type', 'timestamp')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('sender__username', 'meeting__title', 'content')


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    list_display = ('meeting', 'duration', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('meeting__title',)



