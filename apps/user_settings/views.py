from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import UserSettings


@login_required(login_url="login:login")
def settings_view(request):
    """Settings feature: view and update the logged-in user's preferences."""
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        settings_obj.email_notifications = request.POST.get("email_notifications") == "on"
        settings_obj.save()
        messages.success(request, "Settings updated successfully.")
        return redirect("user_settings:settings")

    return render(request, "user_settings/settings.html", {
        "settings_obj": settings_obj,
    })
