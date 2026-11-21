from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from apps.profile.models import Profile


class RegistrationLoginFlowTests(TestCase):
    def test_maintenance_staff_registration_receives_staff_permissions(self):
        response = self.client.post(reverse("register:register"), {
            "full_name": "Campus Maintenance Worker",
            "school_id": "maintenance-1",
            "email": "maintenance@example.edu",
            "contact_number": "09181234567",
            "role": "maintenance_staff",
            "password": "test-password-2026",
            "confirm_password": "test-password-2026",
        })

        self.assertRedirects(response, reverse("login:login"))
        user = get_user_model().objects.get(school_id="maintenance-1")
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, "maintenance_staff")

    def test_registered_user_can_log_in(self):
        response = self.client.post(reverse("register:register"), {
            "full_name": "CampusFix Test Student",
            "school_id": "flow-student-1",
            "email": "flow.student@example.edu",
            "contact_number": "09171234567",
            "role": "student",
            "password": "test-password-2026",
            "confirm_password": "test-password-2026",
        })

        self.assertRedirects(response, reverse("login:login"))
        user = get_user_model().objects.get(school_id="flow-student-1")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.full_name, "CampusFix Test Student")

        response = self.client.post(reverse("login:login"), {
            "school_id": user.school_id,
            "password": "test-password-2026",
        })

        self.assertRedirects(response, reverse("home:home"))
        self.assertEqual(str(user.pk), self.client.session["_auth_user_id"])
