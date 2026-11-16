from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra profile information for a user, owned by the Profile feature."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile_extra",
    )
    full_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="profile/", blank=True, null=True)

    def __str__(self):
        return self.full_name or str(self.user)
