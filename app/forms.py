from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.email = email
        user.username = email
        if commit:
            user.save()
        return user
    
class ResumeUploadForm(forms.Form):
    resume = forms.FileField(label="Upload your resume (PDF only)", required=True)

    def clean_file(self):
        f = self.cleaned_data["resume"]

        if f.content_type not in ["application/pdf"]:
            raise forms.ValidationError("Only PDF files are allowed.")

        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File size must be under 10MB.")
        
        return f