from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.home.models import Notification, RepairRequest


@login_required(login_url="login:login")
def home_view(request):
    """Home feature: the main authenticated landing screen with quick stats."""
    user = request.user
    available_requests = RepairRequest.objects.none()

    if user.role == "admin":
        total_tickets = RepairRequest.objects.count()
        open_tickets = RepairRequest.objects.filter(status="pending").count()
        in_progress = RepairRequest.objects.filter(status="in_progress").count()
        resolved = RepairRequest.objects.filter(status="finished").count()
    elif user.role == "maintenance_staff":
        available_requests = RepairRequest.objects.filter(
            status__in=RepairRequest.ACTIVE_STATUSES,
            assigned_staff__isnull=True,
        ).select_related("reporter", "room__building").order_by("-created_at")
        total_tickets = RepairRequest.objects.count()
        open_tickets = RepairRequest.objects.filter(status="pending").count()
        in_progress = RepairRequest.objects.filter(
            assigned_staff=user,
            status="in_progress",
        ).count()
        resolved = RepairRequest.objects.filter(
            assigned_staff=user,
            status="finished",
        ).count()
    else:
        total_tickets = RepairRequest.objects.filter(reporter=user).count()
        open_tickets = RepairRequest.objects.filter(reporter=user, status="pending").count()
        in_progress = RepairRequest.objects.filter(reporter=user, status="in_progress").count()
        resolved = RepairRequest.objects.filter(reporter=user, status="finished").count()

    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    return render(request, "home/home.html", {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "in_progress": in_progress,
        "resolved": resolved,
        "unread_count": unread_count,
        "available_requests": available_requests,
        "is_admin": user.role == "admin",
        "is_maintenance_staff": user.role == "maintenance_staff",
    })
