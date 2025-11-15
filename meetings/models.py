from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Meeting(models.Model):
    MEETING_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_meetings')
    participants = models.ManyToManyField(User, related_name='participated_meetings', blank=True)
    scheduled_time = models.DateTimeField()
    duration = models.DurationField(help_text="Meeting duration in minutes")
    status = models.CharField(max_length=20, choices=MEETING_STATUS_CHOICES, default='scheduled')
    is_public = models.BooleanField(default=False)
    password = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_scheduled(self):
        return self.status == 'scheduled'
    
    @property
    def is_ended(self):
        return self.status == 'ended'
    
    def start_meeting(self):
        self.status = 'active'
        self.save()
    
    def end_meeting(self):
        self.status = 'ended'
        self.ended_at = timezone.now()
        self.save()


class MeetingRecording(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='recordings')
    file = models.FileField(upload_to='recordings/')
    duration = models.DurationField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recording for {self.meeting.title}"


class MeetingMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    file = models.FileField(upload_to='meeting_files/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class MeetingParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='meeting_participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_audio_enabled = models.BooleanField(default=True)
    is_video_enabled = models.BooleanField(default=True)
    is_screen_sharing = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['meeting', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.meeting.title}"



