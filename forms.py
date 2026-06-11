import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Review


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    mobile = forms.CharField(
        max_length=15,
        required=True,
        label='Mobile number',
        help_text='10-digit Indian mobile (for order SMS updates)',
        widget=forms.TextInput(attrs={'placeholder': '9876543210'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'mobile', 'password1', 'password2')

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        digits = re.sub(r'\D', '', mobile)
        if len(digits) != 10 or digits[0] not in '6789':
            raise forms.ValidationError('Enter a valid 10-digit Indian mobile number.')
        return digits


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (5, '★★★★★'),
        (4, '★★★★'),
        (3, '★★★'),
        (2, '★★'),
        (1, '★'),
    ]

    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Your Rating',
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']


class SupportContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Your name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'you@example.com'}))
    subject = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'How can we help?'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Describe your issue…', 'rows': 5}))
