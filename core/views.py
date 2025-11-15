from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Q
from meetings.models import Meeting
from accounts.models import User


class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['recent_meetings'] = Meeting.objects.filter(
                participants=self.request.user
            ).order_by('-created_at')[:5]
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's meetings
        hosted_meetings = Meeting.objects.filter(host=user).order_by('-created_at')[:5]
        participated_meetings = Meeting.objects.filter(participants=user).exclude(host=user).order_by('-created_at')[:5]
        
        # Get active meetings
        active_meetings = Meeting.objects.filter(
            status='active',
            participants=user
        )
        
        context.update({
            'hosted_meetings': hosted_meetings,
            'participated_meetings': participated_meetings,
            'active_meetings': active_meetings,
            'total_meetings': Meeting.objects.filter(participants=user).count(),
        })
        
        return context


@login_required
def search_meetings(request):
    query = request.GET.get('q', '')
    meetings = []
    
    if query:
        meetings = Meeting.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_public=True
        ).order_by('-created_at')[:10]
    
    context = {
        'meetings': meetings,
        'query': query,
    }
    return render(request, 'core/search.html', context)
