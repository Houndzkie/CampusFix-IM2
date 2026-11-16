from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Profile


@login_required(login_url="login:login")
def profile_view(request):
    """Profile feature: view and update the logged-in user's profile info."""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "").strip()
        profile.bio = request.POST.get("bio", "").strip()

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]

        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile:profile")

    return render(request, "profile/profile.html", {
        "profile": profile,
    })
