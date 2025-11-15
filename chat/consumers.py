import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatMessage
from meetings.models import Meeting, MeetingParticipant


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.meeting_group_name = f'meeting_{self.meeting_id}'
        
        # Join meeting group
        await self.channel_layer.group_add(
            self.meeting_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send meeting participants update
        await self.send_participants_update()
    
    async def disconnect(self, close_code):
        # Leave meeting group
        await self.channel_layer.group_discard(
            self.meeting_group_name,
            self.channel_name
        )
        
        # Send participants update
        await self.send_participants_update()
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'participant_update':
            await self.handle_participant_update(text_data_json)
        elif message_type == 'webrtc_signal':
            await self.handle_webrtc_signal(text_data_json)
    
    async def handle_chat_message(self, data):
        content = data['content']
        message_type = data.get('message_type', 'text')
        recipient_id = data.get('recipient_id', None)
        
        # Save message to database
        message = await self.save_message(content, message_type, recipient_id)
        
        # Prepare message data
        message_data = {
            'id': message.id,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'sender_full_name': message.sender.full_name,
            'content': message.content,
            'message_type': message.message_type,
            'timestamp': message.timestamp.isoformat(),
            'recipient_id': message.recipient.id if message.recipient else None,
            'recipient_name': message.recipient.username if message.recipient else None,
        }
        
        if recipient_id:
            # Private message - send only to sender and recipient via group (filtered on client)
            # Note: For true privacy, you'd need to track user channels separately
            await self.channel_layer.group_send(
                self.meeting_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )
        else:
            # Public message - send to all participants
            await self.channel_layer.group_send(
                self.meeting_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )
    
    async def handle_participant_update(self, data):
        # Broadcast participant status update
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'participant_update',
                'participant': data['participant']
            }
        )
    
    async def handle_webrtc_signal(self, data):
        # Broadcast WebRTC signal to other participants
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'webrtc_signal',
                'signal': data['signal'],
                'target': data.get('target'),
                'sender': self.scope['user'].username if self.scope['user'] != AnonymousUser() else None
            }
        )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def participant_update(self, event):
        # Send participant update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'participant_update',
            'participant': event['participant']
        }))
    
    async def webrtc_signal(self, event):
        # Send WebRTC signal to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'webrtc_signal',
            'signal': event['signal'],
            'target': event.get('target'),
            'sender': event.get('sender')
        }))
    
    async def participants_list(self, event):
        # Send participants list to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'participants_list',
            'participants': event['participants']
        }))
    
    @database_sync_to_async
    def save_message(self, content, message_type, recipient_id=None):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        meeting = Meeting.objects.get(id=self.meeting_id)
        recipient = None
        
        if recipient_id:
            try:
                recipient = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                pass
        
        return ChatMessage.objects.create(
            meeting=meeting,
            sender=self.scope['user'],
            recipient=recipient,
            content=content,
            message_type=message_type
        )
    
    
    async def send_participants_update(self):
        participants = await self.get_meeting_participants()
        await self.channel_layer.group_send(
            self.meeting_group_name,
            {
                'type': 'participants_list',
                'participants': participants
            }
        )
    
    @database_sync_to_async
    def get_meeting_participants(self):
        meeting = Meeting.objects.get(id=self.meeting_id)
        participants = []
        for participant in meeting.meeting_participants.all():
            participants.append({
                'id': participant.user.id,
                'username': participant.user.username,
                'full_name': participant.user.full_name,
                'is_audio_enabled': participant.is_audio_enabled,
                'is_video_enabled': participant.is_video_enabled,
                'is_screen_sharing': participant.is_screen_sharing,
            })
        return participants



