from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
import os

def resume_upload_path(instance, filename):
    user = instance.user
    
    # Get name fields from user
    last = (user.last_name or "Last").strip().replace(" ", "_")
    first = (user.first_name or "First").strip().replace(" ", "_")
    
    filename = f"{last}_{first}_Resume.pdf"
    return f"resumes/{user.id}/{filename}"

class Resume(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to=resume_upload_path)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.get_full_name()} Resume"
