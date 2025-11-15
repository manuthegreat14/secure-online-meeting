from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'meeting', 'message_type', 'timestamp', 'is_read')
    list_filter = ('message_type', 'is_read', 'timestamp')
    search_fields = ('sender__username', 'meeting__title', 'content')
    readonly_fields = ('timestamp',)



