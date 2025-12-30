from allauth.account.forms import LoginForm
from django import forms

class CustomLoginForm(LoginForm):
    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError:
            raise forms.ValidationError("Seu e-mail ou senha estão errados, tente novamente")

from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full bg-surface border border-white/10 rounded-lg p-4 text-text-main focus:border-accent focus:ring-1 focus:ring-accent outline-none transition-colors',
                'rows': '4',
                'placeholder': 'Escreva seu comentário...'
            })
        }
        labels = {
            'content': ''
        }
