from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.http import FileResponse
from django.utils import timezone

from .forms import SignUpForm, ResumeUploadForm
from .models import Resume

def is_board(user):
    return user.is_authenticated and user.groups.filter(name="Board").exists()

def index(request):
    return render(request, "app/index.html")

def signup(request):
    # Handles user registration with first/last name + email
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # create user
            # Add new user to "Member" group automatically
            member_group, _ = Group.objects.get_or_create(name="Member")
            user.groups.add(member_group)
            login(request, user)
            return redirect("my_resume")
    else:
        form = SignUpForm()

    return render(request, "app/signup.html", {"form": form})

@login_required
def my_resume(request):
    resume = Resume.objects.filter(user=request.user).first()
    # Show the user's resume if exists, else prompt to upload
    return render(request, "app/my_resume.html", {"resume": resume})

@login_required
def upload_resume(request):
    resume = Resume.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["resume"]

            # Create Resume entry if doesn't exist yet
            if not resume:
                resume = Resume.objects.create(user=request.user)

            # Save file with dynamic name
            resume.file.save(
                resume.file.field.generate_filename(resume, file.name),
                file,
                save=True
            )
            resume.updated_at = timezone.now()
            resume.save()

            return redirect("my_resume")
    else:
        form = ResumeUploadForm()

    return render(request, "app/upload.html", {"form": form})

@user_passes_test(is_board)
def board_list(request):
    # Query all uploaded resumes, order alphabetically by user name
    resumes = Resume.objects.select_related("user").order_by("user__last_name", "user__first_name")
    return render(request, "app/board_list.html", {"resumes": resumes})

@user_passes_test(is_board)
def board_download_zip(request):
    """
    Creates an in-memory ZIP file of all resume PDFs and downloads it.
    """
    import io, zipfile, os

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for resume in Resume.objects.select_related("user"):
            if resume.file:
                abs_path = resume.file.path
                if os.path.exists(abs_path):
                    # Name inside zip: Last_First_Resume.pdf
                    user = resume.user
                    last = user.last_name.replace(" ", "_")
                    first = user.first_name.replace(" ", "_")
                    filename = f"{last}_{first}_Resume.pdf"

                    zipf.write(abs_path, filename)

    memory_file.seek(0)

    return FileResponse(memory_file, as_attachment=True, filename="resume_book.zip")
