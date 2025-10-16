from django import forms
from django.contrib.auth.forms import AuthenticationForm

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class LoginForm(AuthenticationForm):
    pass