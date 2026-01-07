"""
Training Module Forms
"""
from django import forms
from django.contrib.auth.models import User
from .models import (
    TrainingRecord, PracticalEvaluation, TrainingSession
)


class TrainingRecordForm(forms.ModelForm):
    """Form for uploading training records"""
    
    class Meta:
        model = TrainingRecord
        fields = [
            'requirement',
            'completion_date',
            'instructor_name',
            'certificate_document',
            'hours_completed',
            'notes'
        ]
        widgets = {
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'requirement': forms.Select(attrs={'class': 'form-control'}),
            'instructor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_document': forms.FileInput(attrs={'class': 'form-control'}),
            'hours_completed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_certificate_document(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('certificate_document')
        
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 10MB')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            ext = file.name.lower().split('.')[-1]
            if f'.{ext}' not in allowed_extensions:
                raise forms.ValidationError(
                    'Only PDF and image files are allowed'
                )
        
        return file


class SignOffForm(forms.ModelForm):
    """Form for Training Officers to sign off on training"""
    
    class Meta:
        model = TrainingRecord
        fields = ['verification_notes']
        widgets = {
            'verification_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notes about verification (optional)'
            }),
        }


class PracticalEvaluationForm(forms.ModelForm):
    """Form for conducting practical evaluations"""
    
    class Meta:
        model = PracticalEvaluation
        fields = [
            'member',
            'evaluation_type',
            'skills_checklist',
            'result',
            'overall_score',
            'strengths',
            'areas_for_improvement',
            'recommendations',
            'follow_up_required',
            'follow_up_date',
            'notes'
        ]
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'evaluation_type': forms.Select(attrs={'class': 'form-control'}),
            'skills_checklist': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'List skills evaluated and results...'
            }),
            'result': forms.Select(attrs={'class': 'form-control'}),
            'overall_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 1
            }),
            'strengths': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What did the member do well?'
            }),
            'areas_for_improvement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What areas need improvement?'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for continued development'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active members
        self.fields['member'].queryset = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')


class TrainingSessionForm(forms.ModelForm):
    """Form for creating training sessions"""
    
    class Meta:
        model = TrainingSession
        fields = [
            'title',
            'description',
            'session_date',
            'start_time',
            'end_time',
            'location',
            'max_participants',
            'is_mandatory',
            'requirements_covered'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what will be covered in this session...'
            }),
            'session_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Station 1, Training Room'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Leave blank for unlimited'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requirements_covered': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 8
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError('End time must be after start time')
        
        return cleaned_data
