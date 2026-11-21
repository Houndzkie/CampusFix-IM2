from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Building, Notification, RepairRequest,
    RequestComment, RequestPhoto, Room, StatusHistory, User, UserProfile,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("school_id", "full_name", "email", "role", "is_active", "is_staff")
    search_fields = ("school_id", "full_name", "email")
    ordering = ("school_id",)
    fieldsets = (
        (None, {"fields": ("school_id", "password")}),
        ("Personal Info", {"fields": ("full_name", "email", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("school_id", "full_name", "email", "role", "password1", "password2"),
        }),
    )
    readonly_fields = ("created_at",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "contact_number", "department", "updated_at")


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("building_code", "building_name", "total_floors")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_name", "building", "floor_number", "room_type")
    list_filter = ("building",)


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "reporter", "room", "priority", "status", "created_at")
    list_filter = ("status", "priority", "room")
    search_fields = ("title", "description")


@admin.register(RequestPhoto)
class RequestPhotoAdmin(admin.ModelAdmin):
    list_display = ("photo_id", "request", "photo_type", "uploaded_at")


@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ("comment_id", "request", "author", "created_at")


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("history_id", "request", "old_status", "new_status", "changed_by", "changed_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("notification_id", "user", "request", "is_read", "created_at")
    list_filter = ("is_read",)
