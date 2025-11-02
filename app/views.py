import io, zipfile, os

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.http import FileResponse
from django.utils import timezone
from django.db.models import IntegerField, Value
from django.db.models.functions import Cast, Coalesce

from .forms import SignUpForm, ResumeUploadForm
from .models import Resume, Profile
from .utils import current_class_year_choices

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
    # All class years that actually exist among users with resumes
    years_all = (
        Profile.objects
        .filter(user__resume__isnull=False)   # adjust related_name if needed
        .values_list("class_year", flat=True)
        .distinct()
        .order_by("-class_year")              # 4-digit strings sort fine
    )

    years_active = current_class_year_choices()  # e.g. ['2026','2027','2028','2029']

    # Selected years from querystring; default to active if none chosen
    selected_years = request.GET.getlist("years") or years_active

    resumes = (
        Resume.objects
        .select_related("user", "user__profile")
        .filter(user__profile__class_year__in=selected_years)
        .order_by("-user__profile__class_year", "user__last_name", "user__first_name")
    )

    return render(
        request,
        "app/board_list.html",
        {
            "resumes": resumes,
            "years_all": list(years_all),
            "years_active": years_active,
            "selected_years": selected_years,
        },
    )

@user_passes_test(is_board)
def board_download_zip(request):
    # pull same filter as the board list
    selected_years = request.GET.getlist("years")

    qs = Resume.objects.select_related("user", "user__profile")
    if selected_years:
        qs = qs.filter(user__profile__class_year__in=selected_years)

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for resume in qs:
            f = resume.file  # adjust if your FileField is named differently
            if not f or not f.name:
                continue
            abs_path = f.path
            if not os.path.exists(abs_path):
                continue
            user = resume.user
            cy = getattr(user.profile, "class_year", "Unknown")
            base = os.path.basename(abs_path)
            # Include class year in filename for clarity
            arcname = f"{cy}_{base}"
            zipf.write(abs_path, arcname)

    memory_file.seek(0)
    return FileResponse(memory_file, as_attachment=True, filename="resume_book.zip")