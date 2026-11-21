from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

User = get_user_model()


def register_view(request):
    """Register feature: creates a new user account via the custom User model."""
    error_message = None
    form_data = {}

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        school_id = request.POST.get("school_id", "").strip()
        email = request.POST.get("email", "").strip()
        contact_number = request.POST.get("contact_number", "").strip()
        role = request.POST.get("role", "student").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        form_data = {
            "full_name": full_name,
            "school_id": school_id,
            "email": email,
            "contact_number": contact_number,
            "role": role,
        }

        if not full_name or not school_id or not email or not contact_number or not password or not confirm_password:
            error_message = "All fields are required to register."
        elif role not in ("student", "faculty", "maintenance_staff"):
            error_message = "Please select a valid role."
        elif password != confirm_password:
            error_message = "Passwords do not match. Please re-enter."
        elif len(password) < 6:
            error_message = "Password must be at least 6 characters long."
        elif User.objects.filter(school_id=school_id).exists():
            error_message = f"School ID '{school_id}' is already registered."
        elif User.objects.filter(email=email).exists():
            error_message = f"Email '{email}' is already registered."
        else:
            user = User.objects.create_user(
                school_id=school_id,
                email=email,
                full_name=full_name,
                password=password,
                role=role,
                is_staff=(role == "maintenance_staff"),
            )
            # Auto-create a UserProfile for the new user
            from apps.home.models import UserProfile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"contact_number": contact_number},
            )

            messages.success(
                request,
                f"Registration successful for {school_id}! Please log in with your credentials.",
            )
            return redirect("login:login")

    return render(request, "register/register.html", {
        "error_message": error_message,
        "form_data": form_data,
    })
