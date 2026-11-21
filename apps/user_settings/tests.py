from django.test import TestCase
from django.urls import reverse

from apps.home.models import User


class UserSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            school_id="settings-user",
            email="settings@example.edu",
            full_name="Settings User",
            password="test-password",
            role="student",
        )

    def test_settings_page_has_no_dark_mode_toggle(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("user_settings:settings"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="dark_mode"')

    def test_theme_toggle_is_in_shared_header_on_login_page(self):
        response = self.client.get(reverse("login:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="themeToggle"')
