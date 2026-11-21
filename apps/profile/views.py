from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from apps.home.models import RepairRequest, UserProfile

from .models import Profile


@login_required(login_url="login:login")
def profile_view(request):
    """Profile feature: view and update the logged-in user's profile info."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if not profile.full_name:
        profile.full_name = request.user.full_name
        profile.save(update_fields=["full_name"])
    account_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "").strip()
        profile.bio = request.POST.get("bio", "").strip()
        contact_number = request.POST.get("contact_number", "").strip()
        if not contact_number:
            messages.error(request, "Contact number is required.")
            return render(request, "profile/profile.html", {
                "profile": profile,
                "account_profile": account_profile,
                "reported_count": RepairRequest.objects.filter(reporter=request.user).count(),
                "resolved_count": RepairRequest.objects.filter(reporter=request.user, status="finished").count(),
                "assigned_pending_count": RepairRequest.objects.filter(assigned_staff=request.user, status="pending").count(),
                "assigned_in_progress_count": RepairRequest.objects.filter(assigned_staff=request.user, status="in_progress").count(),
                "assigned_finished_count": RepairRequest.objects.filter(assigned_staff=request.user, status="finished").count(),
            })
        account_profile.contact_number = contact_number
        account_profile.save()
        if profile.full_name:
            request.user.full_name = profile.full_name
            request.user.save(update_fields=["full_name"])

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]

        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile:profile")

    return render(request, "profile/profile.html", {
        "profile": profile,
        "account_profile": account_profile,
        "reported_count": RepairRequest.objects.filter(reporter=request.user).count(),
        "resolved_count": RepairRequest.objects.filter(reporter=request.user, status="finished").count(),
        "assigned_pending_count": RepairRequest.objects.filter(assigned_staff=request.user, status="pending").count(),
        "assigned_in_progress_count": RepairRequest.objects.filter(assigned_staff=request.user, status="in_progress").count(),
        "assigned_finished_count": RepairRequest.objects.filter(assigned_staff=request.user, status="finished").count(),
    })


@login_required(login_url="login:login")
def public_profile_view(request, user_id):
    User = get_user_model()
    account = get_object_or_404(User, pk=user_id)
    profile, _ = Profile.objects.get_or_create(user=account)
    if not profile.full_name:
        profile.full_name = account.full_name
        profile.save(update_fields=["full_name"])
    account_profile, _ = UserProfile.objects.get_or_create(user=account)

    context = {
        "account": account,
        "profile": profile,
        "account_profile": account_profile,
        "reported_count": RepairRequest.objects.filter(reporter=account).count(),
        "resolved_count": RepairRequest.objects.filter(reporter=account, status="finished").count(),
        "assigned_pending_count": RepairRequest.objects.filter(assigned_staff=account, status="pending").count(),
        "assigned_in_progress_count": RepairRequest.objects.filter(assigned_staff=account, status="in_progress").count(),
        "assigned_finished_count": RepairRequest.objects.filter(assigned_staff=account, status="finished").count(),
    }
    return render(request, "profile/public_profile.html", context)
