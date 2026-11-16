from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render


def login_view(request):
    """Login feature: authenticates using school_id + password via custom User."""
    error_message = None

    if request.method == "POST":
        school_id = request.POST.get("school_id", "").strip()
        password = request.POST.get("password", "")

        if not school_id or not password:
            error_message = "Please enter both School ID and password."
        else:
            # USERNAME_FIELD is school_id, so authenticate with it
            user = authenticate(request, school_id=school_id, password=password)
            if user is not None:
                login(request, user)
                return redirect("home:home")
            error_message = "Invalid School ID or password. Please try again."

    return render(request, "login/login.html", {
        "error_message": error_message,
    })


def logout_view(request):
    """Logs the current user out and sends them back to the Login screen."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login:login")
