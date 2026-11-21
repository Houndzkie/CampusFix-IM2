from django.urls import path

from . import views

app_name = "profile"

urlpatterns = [
    path("", views.profile_view, name="profile"),
    path("users/<uuid:user_id>/", views.public_profile_view, name="public_profile"),
]
