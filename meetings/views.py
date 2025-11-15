from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Meeting, MeetingParticipant, MeetingMessage
from .forms import MeetingCreateForm, MeetingJoinForm, MeetingUpdateForm
import uuid
import json


class MeetingListView(LoginRequiredMixin, ListView):
    model = Meeting
    template_name = 'meetings/meeting_list.html'
    context_object_name = 'meetings'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Meeting.objects.filter(
            Q(host=self.request.user) | Q(participants=self.request.user)
        ).distinct()
        
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')


class MeetingCreateView(LoginRequiredMixin, CreateView):
    model = Meeting
    form_class = MeetingCreateForm
    template_name = 'meetings/meeting_create.html'
    success_url = reverse_lazy('meetings:meeting_list')
    
    def form_valid(self, form):
        form.instance.host = self.request.user
        messages.success(self.request, 'Meeting created successfully!')
        return super().form_valid(form)


class MeetingUpdateView(LoginRequiredMixin, UpdateView):
    model = Meeting
    form_class = MeetingUpdateForm
    template_name = 'meetings/meeting_update.html'
    success_url = reverse_lazy('meetings:meeting_list')
    
    def get_queryset(self):
        return Meeting.objects.filter(host=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Meeting updated successfully!')
        return super().form_valid(form)


class MeetingDeleteView(LoginRequiredMixin, DeleteView):
    model = Meeting
    template_name = 'meetings/meeting_confirm_delete.html'
    success_url = reverse_lazy('meetings:meeting_list')
    
    def get_queryset(self):
        return Meeting.objects.filter(host=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Meeting deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def meeting_detail(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user is host or participant
    if meeting.host != request.user and request.user not in meeting.participants.all():
        messages.error(request, 'You do not have permission to view this meeting.')
        return redirect('meetings:meeting_list')
    
    context = {
        'meeting': meeting,
        'is_host': meeting.host == request.user,
    }
    return render(request, 'meetings/meeting_detail.html', context)


def join_meeting(request):
    # Check if meeting_id is provided in URL parameters
    meeting_id = request.GET.get('meeting_id')
    
    if request.method == 'POST':
        form = MeetingJoinForm(request.POST)
        if form.is_valid():
            meeting_id = form.cleaned_data['meeting_id']
            password = form.cleaned_data['password']
            
            try:
                # Try to get meeting by ID (handle both UUID and string formats)
                try:
                    meeting = Meeting.objects.get(id=meeting_id)
                except (Meeting.DoesNotExist, ValueError) as e:
                    # Try with UUID conversion if needed
                    try:
                        import uuid
                        meeting_uuid = uuid.UUID(str(meeting_id))
                        meeting = Meeting.objects.get(id=meeting_uuid)
                    except (Meeting.DoesNotExist, ValueError, TypeError):
                        messages.error(request, 'Meeting not found. Please check the Meeting ID.')
                        return render(request, 'meetings/join_meeting.html', {'form': form})
                
                # Check if meeting is public or password matches
                if not meeting.is_public and meeting.password != password:
                    messages.error(request, 'Invalid password for this meeting.')
                    return render(request, 'meetings/join_meeting.html', {'form': form})
                
                # Check if meeting is active or scheduled
                if meeting.status not in ['active', 'scheduled']:
                    messages.error(request, 'This meeting is not available.')
                    return render(request, 'meetings/join_meeting.html', {'form': form})
                
                # If user is not authenticated, redirect to login with next parameter
                if not request.user.is_authenticated:
                    messages.info(request, 'Please log in to join the meeting.')
                    # Store meeting info for after login
                    request.session['next'] = reverse('meetings:join_meeting')
                    request.session['pending_meeting_id'] = str(meeting.pk)
                    return redirect('accounts:login')
                
                # Add user as participant if not already
                if request.user not in meeting.participants.all():
                    meeting.participants.add(request.user)
                
                # Store meeting ID in session for lobby
                request.session['pending_meeting_id'] = str(meeting.pk)
                
                # Redirect to lobby for verification
                return redirect('meetings:lobby', pk=meeting.pk)
                
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                return render(request, 'meetings/join_meeting.html', {'form': form})
        else:
            # Form is invalid - show errors
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill form with meeting_id if provided in URL
        initial_data = {}
        if meeting_id:
            initial_data['meeting_id'] = meeting_id
        form = MeetingJoinForm(initial=initial_data)
    
    return render(request, 'meetings/join_meeting.html', {'form': form})


def join_meeting_direct(request, meeting_id):
    """Direct join URL for meetings - allows joining with just the meeting ID in URL"""
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        
        # Check if meeting is active or scheduled
        if meeting.status not in ['active', 'scheduled']:
            messages.error(request, 'This meeting is not available.')
            return redirect('core:home')
        
        # If meeting is password protected, redirect to join form
        if not meeting.is_public:
            messages.info(request, 'This meeting requires a password.')
            form = MeetingJoinForm(initial={'meeting_id': str(meeting_id)})
            return render(request, 'meetings/join_meeting.html', {'form': form})
        
        # If user is not authenticated, redirect to login with next parameter
        if not request.user.is_authenticated:
            messages.info(request, 'Please log in to join the meeting.')
            return redirect('accounts:login')
        
        # Add user as participant if not already
        if request.user not in meeting.participants.all():
            meeting.participants.add(request.user)
        
        # Store meeting ID in session for lobby
        request.session['pending_meeting_id'] = str(meeting_id)
        
        # Redirect to lobby for verification
        return redirect('meetings:lobby', pk=meeting.pk)
        
    except Meeting.DoesNotExist:
        messages.error(request, 'Meeting not found.')
        return redirect('core:home')


@login_required
def meeting_room(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user is host or participant
    if meeting.host != request.user and request.user not in meeting.participants.all():
        messages.error(request, 'You do not have permission to join this meeting.')
        return redirect('meetings:meeting_list')
    
    # Check if user has verified in lobby for THIS meeting (verification required every time)
    verified = request.session.get(f'meeting_{pk}_verified', False)
    if not verified:
        messages.info(request, 'Please complete verification in the lobby first.')
        return redirect('meetings:lobby', pk=meeting.pk)
    
    # Get or create meeting participant
    participant, created = MeetingParticipant.objects.get_or_create(
        meeting=meeting,
        user=request.user
    )
    
    context = {
        'meeting': meeting,
        'participant': participant,
        'is_host': meeting.host == request.user,
    }
    return render(request, 'meetings/meeting_room.html', context)


@login_required
def start_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk, host=request.user)
    
    if meeting.status == 'scheduled':
        meeting.start_meeting()
        messages.success(request, 'Meeting started successfully!')
    else:
        messages.error(request, 'Meeting cannot be started.')
    
    return redirect('meetings:meeting_room', pk=pk)


@login_required
def end_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk, host=request.user)
    
    if meeting.status == 'active':
        meeting.end_meeting()
        messages.success(request, 'Meeting ended successfully!')
    else:
        messages.error(request, 'Meeting cannot be ended.')
    
    return redirect('meetings:meeting_detail', pk=pk)


@login_required
def leave_meeting(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    if request.user in meeting.participants.all():
        meeting.participants.remove(request.user)
        messages.success(request, 'You have left the meeting.')
    
    # Clear verification session so user must verify again next time
    if f'meeting_{pk}_verified' in request.session:
        del request.session[f'meeting_{pk}_verified']
    
    return redirect('meetings:meeting_list')


@login_required
def get_meeting_participants(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    participants = meeting.meeting_participants.all()
    
    data = []
    for participant in participants:
        data.append({
            'id': participant.user.id,
            'username': participant.user.username,
            'full_name': participant.user.full_name,
            'is_audio_enabled': participant.is_audio_enabled,
            'is_video_enabled': participant.is_video_enabled,
            'is_screen_sharing': participant.is_screen_sharing,
        })
    
    return JsonResponse({'participants': data})


@login_required
def get_meeting_messages(request, pk):
    """Get chat messages for a meeting (public messages + private messages for/to current user)"""
    from chat.models import ChatMessage
    
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Get public messages and private messages for/to current user
    messages = ChatMessage.objects.filter(
        meeting=meeting
    ).filter(
        models.Q(recipient__isnull=True) |  # Public messages
        models.Q(recipient=request.user) |  # Private messages to me
        models.Q(sender=request.user)       # Private messages from me
    ).select_related('sender', 'recipient').order_by('timestamp')[:100]
    
    data = []
    for message in messages:
        data.append({
            'id': message.id,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'sender_full_name': message.sender.full_name,
            'recipient_id': message.recipient.id if message.recipient else None,
            'recipient_name': message.recipient.username if message.recipient else None,
            'content': message.content,
            'message_type': message.message_type,
            'timestamp': message.timestamp.isoformat(),
        })
    
    return JsonResponse({'messages': data})


@login_required
def lobby(request, pk):
    """Lobby page where users verify their identity before entering meeting"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user is host or participant
    if meeting.host != request.user and request.user not in meeting.participants.all():
        messages.error(request, 'You do not have permission to join this meeting.')
        return redirect('meetings:meeting_list')
    
    # Check if meeting is active or scheduled
    if meeting.status not in ['active', 'scheduled']:
        messages.error(request, 'This meeting is not available.')
        return redirect('meetings:meeting_list')
    
    # Verification required every time - no session check to skip
    context = {
        'meeting': meeting,
        'is_host': meeting.host == request.user,
        'user': request.user,
    }
    return render(request, 'meetings/lobby.html', context)


@login_required
@require_POST
def verify_and_enter(request, pk):
    """Verify face match, fullscreen, and captcha, then allow entry"""
    meeting = get_object_or_404(Meeting, pk=pk)
    
    # Check if user is host or participant
    if meeting.host != request.user and request.user not in meeting.participants.all():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    data = json.loads(request.body)
    face_match = data.get('face_match', False)
    is_fullscreen = data.get('is_fullscreen', False)
    network_verified = data.get('network_verified', False)
    captcha_verified = data.get('captcha_verified', False)
    
    # Validate all requirements
    if not face_match:
        return JsonResponse({'success': False, 'error': 'Face verification failed. Your face must match your profile photo.'}, status=400)
    
    if not is_fullscreen:
        return JsonResponse({'success': False, 'error': 'Please enter fullscreen mode'}, status=400)
    
    if not network_verified:
        return JsonResponse({'success': False, 'error': 'Please complete network speed test'}, status=400)
    
    if not captcha_verified:
        return JsonResponse({'success': False, 'error': 'Captcha verification failed'}, status=400)
    
    # Check if user has profile photo
    if not request.user.avatar:
        return JsonResponse({'success': False, 'error': 'Please upload a profile photo first'}, status=400)
    
    # If meeting is scheduled, start it
    if meeting.status == 'scheduled':
        meeting.start_meeting()
    
    # Mark as verified in session (this will be cleared when leaving meeting)
    request.session[f'meeting_{pk}_verified'] = True
    
    return JsonResponse({'success': True, 'redirect_url': reverse('meetings:meeting_room', args=[pk])})


@login_required
@csrf_exempt
@require_POST
@login_required
@csrf_exempt
@require_POST
def verify_face(request):
    """Verify face match with profile photo (no dlib / compiler required)"""
    try:
        data = json.loads(request.body)
        face_image_data = data.get('face_image')

        if not face_image_data:
            return JsonResponse({'success': False, 'error': 'No face image provided'}, status=400)

        user = request.user
        if not user.avatar:
            return JsonResponse({
                'success': False,
                'matched': False,
                'error': 'Please upload a profile photo first. Go to your profile to add one.'
            }, status=400)

        # Decode base64 → OpenCV image
        import cv2, base64, numpy as np
        img_bytes = base64.b64decode(face_image_data.split(',')[1])
        np_bytes = np.frombuffer(img_bytes, np.uint8)
        captured_img = cv2.imdecode(np_bytes, cv2.IMREAD_COLOR)

        # --- Try DeepFace (no dlib required) ---
        try:
            from deepface import DeepFace

            def get_embedding(image, model="Facenet512"):
                return DeepFace.represent(
                    img_path=image,
                    model_name=model,
                    enforce_detection=False
                )[0]["embedding"]

            # Try Facenet512 first
            try:
                emb_avatar = get_embedding(user.avatar.path, model="Facenet512")
                emb_captured = get_embedding(captured_img, model="Facenet512")
            except Exception as e1:
                print(f"[WARN] Facenet512 failed: {e1}")
                # fallback to VGG-Face
                emb_avatar = get_embedding(user.avatar.path, model="VGG-Face")
                emb_captured = get_embedding(captured_img, model="VGG-Face")

            # Cosine similarity
            similarity = float(np.dot(emb_avatar, emb_captured) /
                               (np.linalg.norm(emb_avatar) * np.linalg.norm(emb_captured)))
            matched = similarity > 0.35  # tuned threshold

            return JsonResponse({
                'success': True,
                'matched': matched,
                'similarity': round(similarity, 3),
                'confidence': round(similarity * 100, 2),
                'message': ' Face matched!' if matched else ' Face did not match.'
            })

        except ImportError:
            # --- DeepFace not installed — fallback to imagehash ---
            try:
                from PIL import Image
                import io, imagehash

                avatar_image = Image.open(user.avatar.path)
                image_data = base64.b64decode(face_image_data.split(',')[1])
                captured_image = Image.open(io.BytesIO(image_data))

                # Resize and grayscale
                size = (256, 256)
                avatar_gray = avatar_image.resize(size).convert('L')
                captured_gray = captured_image.resize(size).convert('L')

                avatar_hash = imagehash.average_hash(avatar_gray)
                captured_hash = imagehash.average_hash(captured_gray)
                hamming_distance = avatar_hash - captured_hash

                MATCH_THRESHOLD = 10
                matched = hamming_distance <= MATCH_THRESHOLD
                similarity = max(0, (1 - hamming_distance / 64) * 100)

                return JsonResponse({
                    'success': True,
                    'matched': matched,
                    'confidence': round(similarity, 1),
                    'message': ' Face matched!' if matched else ' Face did not match.'
                })

            except ImportError:
                # --- imagehash not installed — fallback to basic pixel diff ---
                from PIL import Image, ImageStat
                import io

                avatar = Image.open(user.avatar.path).convert('RGB').resize((200, 200))
                image_data = base64.b64decode(face_image_data.split(',')[1])
                captured = Image.open(io.BytesIO(image_data)).convert('RGB').resize((200, 200))

                avatar_gray = avatar.convert('L')
                captured_gray = captured.convert('L')

                pixels1 = np.array(avatar_gray).flatten()
                pixels2 = np.array(captured_gray).flatten()

                mse = np.mean((pixels1 - pixels2) ** 2)
                similarity = max(0, (1 - mse / (255 ** 2)) * 100)
                matched = similarity >= 70

                return JsonResponse({
                    'success': True,
                    'matched': matched,
                    'confidence': round(similarity, 1),
                    'message': ' Face matched!' if matched else ' Face did not match.'
                })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
