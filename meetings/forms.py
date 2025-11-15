from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import Meeting

User = get_user_model()


class MeetingCreateForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'scheduled_time', 'duration', 'is_public', 'password']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            Row(
                Column('scheduled_time', css_class='form-group col-md-6 mb-0'),
                Column('duration', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_public', css_class='form-group col-md-6 mb-0'),
                Column('password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )
    
    def clean_scheduled_time(self):
        scheduled_time = self.cleaned_data.get('scheduled_time')
        if scheduled_time and scheduled_time < timezone.now():
            raise forms.ValidationError("Scheduled time cannot be in the past.")
        return scheduled_time


class MeetingJoinForm(forms.Form):
    meeting_id = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Enter Meeting ID'}))
    password = forms.CharField(max_length=100, required=False, widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password (if required)'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'meeting_id',
            'password',
        )


class MeetingUpdateForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'scheduled_time', 'duration', 'is_public', 'password']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            'description',
            Row(
                Column('scheduled_time', css_class='form-group col-md-6 mb-0'),
                Column('duration', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_public', css_class='form-group col-md-6 mb-0'),
                Column('password', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )
