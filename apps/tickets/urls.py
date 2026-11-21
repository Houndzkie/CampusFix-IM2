from django.urls import path
from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list_view, name="ticket_list"),
    path("reports/active-reporters/", views.active_reporters_view, name="active_reporters"),
    path("create/", views.ticket_create_view, name="ticket_create"),
    path("<uuid:pk>/", views.ticket_detail_view, name="ticket_detail"),
    path("<uuid:pk>/comment/", views.post_comment_view, name="post_comment"),
    path("<uuid:pk>/status/", views.update_status_view, name="update_status"),
    path("<uuid:pk>/take/", views.take_ticket_view, name="take_ticket"),
    path("api/rooms/", views.rooms_by_building_view, name="rooms_by_building"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:notif_id>/read/", views.mark_notification_read_view, name="mark_read"),
    path("notifications/mark-all-read/", views.mark_all_read_view, name="mark_all_read"),
    path("api/unread-count/", views.unread_count_view, name="unread_count"),
]
