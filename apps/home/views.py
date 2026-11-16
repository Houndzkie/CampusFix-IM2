from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.home.models import Notification, RepairRequest


@login_required(login_url="login:login")
def home_view(request):
    """Home feature: the main authenticated landing screen with quick stats."""
    user = request.user

    if user.role in ("admin", "staff"):
        total_tickets = RepairRequest.objects.count()
        open_tickets = RepairRequest.objects.filter(status="open").count()
        in_progress = RepairRequest.objects.filter(status="in_progress").count()
        resolved = RepairRequest.objects.filter(status="resolved").count()
    else:
        total_tickets = RepairRequest.objects.filter(reporter=user).count()
        open_tickets = RepairRequest.objects.filter(reporter=user, status="open").count()
        in_progress = RepairRequest.objects.filter(reporter=user, status="in_progress").count()
        resolved = RepairRequest.objects.filter(reporter=user, status="resolved").count()

    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    return render(request, "home/home.html", {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "in_progress": in_progress,
        "resolved": resolved,
        "unread_count": unread_count,
    })
