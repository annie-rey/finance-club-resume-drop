from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile
from .utils import current_class_year_choices  # your dynamic year function


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name  = forms.CharField(max_length=30, required=True)
    email      = forms.EmailField(max_length=254, required=True)
    class_year = forms.ChoiceField(choices=(), required=True, label="Class Year")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically assign class year options (e.g., 2026–2029)
        self.fields["class_year"].choices = [
            (year, year) for year in current_class_year_choices()
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        # map email to username
        email = self.cleaned_data["email"]
        user.email = email
        user.username = email
        user.first_name = self.cleaned_data["first_name"].strip().title()
        user.last_name = self.cleaned_data["last_name"].strip().title()

        if commit:
            user.save()

            # save class year into Profile
            class_year = self.cleaned_data["class_year"]
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.class_year = class_year
            profile.save()

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