from django.test import TestCase

from apps.home.models import User


class UserManagerTests(TestCase):
    def test_create_superuser_defaults_to_admin_role(self):
        user = User.objects.create_superuser(
            school_id="admin-1",
            email="admin@example.edu",
            full_name="CampusFix Admin",
            password="test-password",
        )

        self.assertEqual(user.role, "admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
