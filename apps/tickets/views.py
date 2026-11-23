"""
Tickets app views — covers the full ticket lifecycle:
  - Ticket list (reporter sees own; staff/admin sees all)
  - Ticket create (with cascading building→room and multi-photo)
  - Ticket detail (comments, status history timeline)
  - Post comment
  - Update status (admin/staff only) → auto StatusHistory + Notification
  - Notifications list + mark-read
  - AJAX endpoint: rooms by building
"""
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db.models import Count, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError

from apps.home.models import (
    Building,
    Notification,
    RepairRequest,
    RequestComment,
    RequestPhoto,
    Room,
    StatusHistory,
    User,
)

PRIORITY_CHOICES = ["low", "medium", "high", "urgent"]
STATUS_CHOICES = ["pending", "in_progress", "finished"]
MAX_PHOTO_COUNT = 5
MAX_PHOTO_SIZE = 5 * 1024 * 1024
PHOTO_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
ACTIVE_REQUEST_STATUSES = RepairRequest.ACTIVE_STATUSES
MAINTENANCE_ROLES = ("admin", "maintenance_staff")


# ─── Helper ─────────────────────────────────────────────────────────────────

def _notify(user, request_obj, message):
    """Create an in-app Notification record."""
    Notification.objects.create(
        user=user,
        request=request_obj,
        message=message,
    )


# ─── Ticket List ────────────────────────────────────────────────────────────

@login_required(login_url="login:login")
def ticket_list_view(request):
    """Reporters see their tickets, staff see available work, and admins see all."""
    user = request.user
    is_admin = user.role == "admin"
    is_maintenance_staff = user.role == "maintenance_staff"
    if is_admin:
        tickets = RepairRequest.objects.select_related(
            "reporter", "assigned_staff", "room__building"
        ).order_by("-created_at")
    elif is_maintenance_staff:
        tickets = RepairRequest.objects.filter(
            status__in=ACTIVE_REQUEST_STATUSES,
            assigned_staff__isnull=True,
        ).select_related(
            "reporter", "room__building"
        ).order_by("-created_at")
    else:
        tickets = RepairRequest.objects.filter(reporter=user).select_related(
            "room__building"
        ).order_by("-created_at")

    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    return render(request, "tickets/ticket_list.html", {
        "tickets": tickets,
        "unread_count": unread_count,
        "is_admin": is_admin,
        "is_maintenance_staff": is_maintenance_staff,
    })


def active_reporters_queryset():
    active_reporter_ids = RepairRequest.objects.filter(
        status__in=ACTIVE_REQUEST_STATUSES
    ).values("reporter_id")
    return User.objects.filter(
        user_id__in=Subquery(active_reporter_ids)
    ).annotate(
        active_ticket_count=Count(
            "reported_requests",
            filter=Q(reported_requests__status__in=ACTIVE_REQUEST_STATUSES),
        )
    ).order_by("full_name", "school_id")


@login_required(login_url="login:login")
def active_reporters_view(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to view reports.")
        return redirect("tickets:ticket_list")

    return render(request, "tickets/active_reporters.html", {
        "reporters": active_reporters_queryset(),
    })


# ─── Ticket Create ──────────────────────────────────────────────────────────

@login_required(login_url="login:login")
def ticket_create_view(request):
    buildings = Building.objects.order_by("building_name")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "medium")
        building_id = request.POST.get("building_id")
        room_id = request.POST.get("room_id")
        photos = request.FILES.getlist("photos")

        errors = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if not photos:
            errors.append("At least one issue photo is required.")
        if not building_id or not room_id:
            errors.append("Please select a building and room.")
        if priority not in PRIORITY_CHOICES:
            errors.append("Please select a valid priority.")
        if len(photos) > MAX_PHOTO_COUNT:
            errors.append(f"You can upload up to {MAX_PHOTO_COUNT} photos.")
        for photo_file in photos:
            if photo_file.size > MAX_PHOTO_SIZE:
                errors.append(f"Each photo must be no larger than {MAX_PHOTO_SIZE // (1024 * 1024)} MB.")
                break
            try:
                with Image.open(photo_file) as image:
                    image_format = image.format
                    image.verify()
                if image_format not in PHOTO_FORMATS:
                    errors.append("Photos must be JPG, PNG, or WEBP images.")
                    break
                photo_file.seek(0)
            except (UnidentifiedImageError, OSError):
                errors.append("One or more uploaded files are not valid images.")
                break

        room = None
        if building_id and room_id:
            try:
                room = Room.objects.get(pk=room_id, building_id=building_id)
            except Room.DoesNotExist:
                errors.append("The selected room does not belong to that building.")
            except ValueError:
                errors.append("Invalid building or room.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "tickets/ticket_create.html", {
                "buildings": buildings,
                "priority_choices": PRIORITY_CHOICES,
                "form_data": request.POST,
                "max_photo_count": MAX_PHOTO_COUNT,
            })

        ticket = RepairRequest.objects.create(
            reporter=request.user,
            room=room,
            title=title,
            description=description,
            priority=priority,
            status="pending",
        )

        # Save initial StatusHistory
        StatusHistory.objects.create(
            request=ticket,
            changed_by=request.user,
            old_status=None,
            new_status="pending",
            remarks="Ticket submitted.",
        )

        # Use Django's configured storage so media can be local or remote.
        for photo_file in photos:
            with Image.open(photo_file) as image:
                photo_type = PHOTO_FORMATS[image.format]
            photo_file.seek(0)
            saved_path = default_storage.save(
                f"request_photos/{ticket.request_id}/{Path(photo_file.name).name}",
                photo_file,
            )
            RequestPhoto.objects.create(
                request=ticket,
                photo_url=default_storage.url(saved_path),
                photo_type="issue",
            )

        messages.success(request, f"Ticket '{title}' submitted successfully!")
        return redirect("tickets:ticket_detail", pk=ticket.request_id)

    return render(request, "tickets/ticket_create.html", {
        "buildings": buildings,
        "priority_choices": PRIORITY_CHOICES,
        "form_data": {},
        "max_photo_count": MAX_PHOTO_COUNT,
    })


# ─── Ticket Detail ──────────────────────────────────────────────────────────

@login_required(login_url="login:login")
def ticket_detail_view(request, pk):
    ticket = get_object_or_404(
        RepairRequest.objects.select_related(
            "reporter", "assigned_staff", "room__building"
        ),
        pk=pk,
    )
    # Reporters can only see their own tickets
    if request.user.role not in MAINTENANCE_ROLES and ticket.reporter != request.user:
        messages.error(request, "You do not have permission to view this ticket.")
        return redirect("tickets:ticket_list")

    comments = ticket.comments.select_related("author").order_by("created_at")
    history = ticket.status_history.select_related("changed_by").order_by("changed_at")
    photos = ticket.photos.all()
    staff_users = User.objects.filter(role__in=MAINTENANCE_ROLES).order_by("full_name")
    issue_photos = ticket.photos.filter(photo_type="issue")
    proof_photos = ticket.photos.filter(photo_type="proof")
    existing_proof_count = proof_photos.count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, "tickets/ticket_detail.html", {
        "ticket": ticket,
        "comments": comments,
        "history": history,
        "photos": photos,
        "issue_photos": issue_photos,
        "proof_photos": proof_photos,
        "existing_proof_count": existing_proof_count,
        "max_photo_count": MAX_PHOTO_COUNT,
        "staff_users": staff_users,
        "status_choices": STATUS_CHOICES,
        "unread_count": unread_count,
        "can_edit": (
            ticket.reporter == request.user
            and ticket.assigned_staff is None
            and ticket.status == "pending"
        ),
        "can_take": (
            ticket.assigned_staff is None
            and ticket.status in ACTIVE_REQUEST_STATUSES
        ),
    })


@login_required(login_url="login:login")
def edit_ticket_view(request, pk):
    ticket = get_object_or_404(
        RepairRequest.objects.select_related("reporter", "room__building"),
        pk=pk,
    )
    if ticket.reporter != request.user:
        messages.error(request, "Only the reporter can edit this ticket.")
        return redirect("tickets:ticket_detail", pk=pk)
    if ticket.assigned_staff or ticket.status != "pending":
        messages.error(request, "This ticket can no longer be edited because it has been taken.")
        return redirect("tickets:ticket_detail", pk=pk)

    buildings = Building.objects.order_by("building_code")
    existing_issue_photos = ticket.photos.filter(photo_type="issue")
    existing_issue_count = existing_issue_photos.count()
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "medium").strip()
        building_id = request.POST.get("building_id")
        room_id = request.POST.get("room_id")
        photos = request.FILES.getlist("photos")
        errors = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")
        if priority not in PRIORITY_CHOICES:
            errors.append("Please select a valid priority.")
        if not building_id or not room_id:
            errors.append("Please select a building and room.")
        if existing_issue_count + len(photos) > MAX_PHOTO_COUNT:
            errors.append(f"A ticket can have no more than {MAX_PHOTO_COUNT} issue photos.")
        for photo_file in photos:
            if photo_file.size > MAX_PHOTO_SIZE:
                errors.append(f"Each photo must be no larger than {MAX_PHOTO_SIZE // (1024 * 1024)} MB.")
                break
            try:
                with Image.open(photo_file) as image:
                    image_format = image.format
                    image.verify()
                if image_format not in PHOTO_FORMATS:
                    errors.append("Photos must be JPG, PNG, or WEBP images.")
                    break
                photo_file.seek(0)
            except (UnidentifiedImageError, OSError):
                errors.append("One or more uploaded files are not valid images.")
                break

        room = None
        if building_id and room_id:
            try:
                room = Room.objects.get(pk=room_id, building_id=building_id)
            except (Room.DoesNotExist, ValueError):
                errors.append("The selected room does not belong to that building.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, "tickets/ticket_edit.html", {
                "ticket": ticket,
                "buildings": buildings,
                "priority_choices": PRIORITY_CHOICES,
                "existing_issue_photos": existing_issue_photos,
                "existing_issue_count": existing_issue_count,
                "max_photo_count": MAX_PHOTO_COUNT,
            })

        ticket.title = title
        ticket.description = description
        ticket.priority = priority
        ticket.room = room
        ticket.save()

        for photo_file in photos:
            with Image.open(photo_file) as image:
                photo_type = PHOTO_FORMATS[image.format]
            photo_file.seek(0)
            saved_path = default_storage.save(
                f"request_photos/{ticket.request_id}/{Path(photo_file.name).name}",
                photo_file,
            )
            RequestPhoto.objects.create(
                request=ticket,
                photo_url=default_storage.url(saved_path),
                photo_type="issue",
            )

        messages.success(request, "Ticket details updated.")
        return redirect("tickets:ticket_detail", pk=pk)

    return render(request, "tickets/ticket_edit.html", {
        "ticket": ticket,
        "buildings": buildings,
        "priority_choices": PRIORITY_CHOICES,
        "existing_issue_photos": existing_issue_photos,
        "existing_issue_count": existing_issue_count,
        "max_photo_count": MAX_PHOTO_COUNT,
    })


# ─── Post Comment ───────────────────────────────────────────────────────────

@login_required(login_url="login:login")
@require_POST
def post_comment_view(request, pk):
    ticket = get_object_or_404(RepairRequest, pk=pk)
    if request.user.role not in MAINTENANCE_ROLES and ticket.reporter != request.user:
        messages.error(request, "You do not have permission to comment on this ticket.")
        return redirect("tickets:ticket_list")

    body = request.POST.get("body", "").strip()
    if not body:
        messages.error(request, "Comment cannot be empty.")
        return redirect("tickets:ticket_detail", pk=pk)

    RequestComment.objects.create(
        request=ticket,
        author=request.user,
        body=body,
    )

    recipients = set()
    if request.user != ticket.reporter:
        recipients.add(ticket.reporter)
    if ticket.assigned_staff and request.user != ticket.assigned_staff:
        recipients.add(ticket.assigned_staff)
    elif request.user == ticket.reporter:
        recipients.update(User.objects.filter(role__in=MAINTENANCE_ROLES))
    for recipient in recipients:
        _notify(
            recipient,
            ticket,
            f"New comment on ticket '{ticket.title}' by {request.user.full_name}.",
        )

    messages.success(request, "Comment posted.")
    return redirect("tickets:ticket_detail", pk=pk)


# ─── Update Status (admin/staff) ────────────────────────────────────────────

@login_required(login_url="login:login")
@require_POST
def update_status_view(request, pk):
    if request.user.role not in MAINTENANCE_ROLES:
        messages.error(request, "You do not have permission to update ticket status.")
        return redirect("tickets:ticket_detail", pk=pk)

    ticket = get_object_or_404(RepairRequest, pk=pk)
    new_status = request.POST.get("new_status", "").strip()
    remarks = request.POST.get("remarks", "").strip()
    assigned_staff_id = request.POST.get("assigned_staff_id", "").strip()
    proof_photos = request.FILES.getlist("proof_photos")

    if new_status not in STATUS_CHOICES:
        messages.error(request, "Invalid status.")
        return redirect("tickets:ticket_detail", pk=pk)
    existing_proof_count = ticket.photos.filter(photo_type="proof").count()
    if existing_proof_count + len(proof_photos) > MAX_PHOTO_COUNT:
        messages.error(request, f"A ticket can have no more than {MAX_PHOTO_COUNT} proof photos.")
        return redirect("tickets:ticket_detail", pk=pk)
    if new_status == "finished":
        if existing_proof_count == 0 and not proof_photos:
            messages.error(request, "At least one proof photo is required to finish this ticket.")
            return redirect("tickets:ticket_detail", pk=pk)

    old_status = ticket.status

    validated_proofs = []
    for photo_file in proof_photos:
        try:
            with Image.open(photo_file) as image:
                image_format = image.format
                image.verify()
            if image_format not in PHOTO_FORMATS:
                messages.error(request, "Proof photos must be JPG, PNG, or WEBP images.")
                return redirect("tickets:ticket_detail", pk=pk)
            if photo_file.size > MAX_PHOTO_SIZE:
                messages.error(request, f"Each proof photo must be no larger than {MAX_PHOTO_SIZE // (1024 * 1024)} MB.")
                return redirect("tickets:ticket_detail", pk=pk)
            photo_file.seek(0)
            validated_proofs.append(photo_file)
        except (UnidentifiedImageError, OSError):
            messages.error(request, "One or more proof photos are not valid images.")
            return redirect("tickets:ticket_detail", pk=pk)

    # Assign staff if provided
    if assigned_staff_id:
        try:
            staff = User.objects.get(pk=assigned_staff_id, role__in=MAINTENANCE_ROLES)
            ticket.assigned_staff = staff
        except User.DoesNotExist:
            pass

    ticket.status = new_status
    if new_status == "finished":
        ticket.completed_at = timezone.now()
    else:
        ticket.completed_at = None
    ticket.save()

    for photo_file in validated_proofs:
        with Image.open(photo_file) as image:
            photo_type = PHOTO_FORMATS[image.format]
        photo_file.seek(0)
        saved_path = default_storage.save(
            f"proof_photos/{ticket.request_id}/{Path(photo_file.name).name}",
            photo_file,
        )
        RequestPhoto.objects.create(
            request=ticket,
            photo_url=default_storage.url(saved_path),
            photo_type="proof",
        )

    # Audit trail
    StatusHistory.objects.create(
        request=ticket,
        changed_by=request.user,
        old_status=old_status,
        new_status=new_status,
        remarks=remarks or None,
    )

    # Notify reporter
    _notify(
        ticket.reporter,
        ticket,
        f"Your ticket '{ticket.title}' status changed from '{old_status}' to '{new_status}'.",
    )

    messages.success(request, f"Ticket status updated to '{new_status}'.")
    return redirect("tickets:ticket_detail", pk=pk)


@login_required(login_url="login:login")
@require_POST
def take_ticket_view(request, pk):
    if request.user.role not in MAINTENANCE_ROLES:
        messages.error(request, "You do not have permission to take this ticket.")
        return redirect("tickets:ticket_detail", pk=pk)

    ticket = get_object_or_404(RepairRequest, pk=pk)
    claimed = RepairRequest.objects.filter(
        pk=pk,
        status__in=ACTIVE_REQUEST_STATUSES,
        assigned_staff__isnull=True,
    ).update(
        assigned_staff=request.user,
        status="in_progress",
        completed_at=None,
        updated_at=timezone.now(),
    )
    if not claimed:
        messages.error(request, "This request is no longer available to take.")
        return redirect("tickets:ticket_detail", pk=pk)

    StatusHistory.objects.create(
        request=ticket,
        changed_by=request.user,
        old_status=ticket.status,
        new_status="in_progress",
        remarks="Ticket taken by maintenance staff.",
    )
    _notify(
        ticket.reporter,
        ticket,
        f"Your ticket '{ticket.title}' is now being handled by {request.user.full_name}.",
    )
    messages.success(request, "You have taken this ticket and it is now in progress.")
    return redirect("tickets:ticket_detail", pk=pk)


# ─── AJAX: Rooms by Building ─────────────────────────────────────────────────

@login_required(login_url="login:login")
def rooms_by_building_view(request):
    building_id = request.GET.get("building_id")
    if not building_id:
        return JsonResponse({"rooms": []})
    rooms = list(
        Room.objects.filter(building_id=building_id).values("room_id", "room_name", "floor_number")
    )
    return JsonResponse({"rooms": rooms})


# ─── Notifications ──────────────────────────────────────────────────────────

@login_required(login_url="login:login")
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).select_related(
        "request"
    ).order_by("-created_at")
    unread_count = notifs.filter(is_read=False).count()
    return render(request, "tickets/notifications.html", {
        "notifications": notifs,
        "unread_count": unread_count,
    })


@login_required(login_url="login:login")
@require_POST
def mark_notification_read_view(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    next_url = request.POST.get("next") or "tickets:notifications"
    if next_url == "tickets:notifications":
        return redirect("tickets:notifications")
    return redirect(next_url)


@login_required(login_url="login:login")
@require_POST
def mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("tickets:notifications")


# ─── Unread count (AJAX for navbar badge) ────────────────────────────────────

@login_required(login_url="login:login")
def unread_count_view(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"unread_count": count})
