from django import forms
from .models import Subscriber

class SubscriberForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'nl-input',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'nl-input',
                'placeholder': 'Your name (optional)'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Subscriber.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError('This email is already subscribed!')
        return email