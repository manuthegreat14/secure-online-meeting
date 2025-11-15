from django.db import models
from django.contrib.auth import get_user_model
from meetings.models import Meeting

User = get_user_model()


class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('system', 'System'),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True, help_text="If set, this is a private message. If null, it's a public message.")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['meeting', 'recipient', 'timestamp']),
        ]
    
    def __str__(self):
        recipient_info = f" to {self.recipient.username}" if self.recipient else " (public)"
        return f"{self.sender.username}{recipient_info}: {self.content[:50]}"
    
    @property
    def is_private(self):
        return self.recipient is not None



