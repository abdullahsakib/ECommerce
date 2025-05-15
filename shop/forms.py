from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Review

class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'password1', 'password2']

class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['review_text']
