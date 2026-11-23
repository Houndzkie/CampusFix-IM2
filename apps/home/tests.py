from django.test import TestCase

from django.urls import reverse

from apps.home.models import Building, RepairRequest, Room, User


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


class MaintenanceDashboardTests(TestCase):
    def test_staff_dashboard_lists_only_unclaimed_pending_requests(self):
        staff = User.objects.create_user(
            school_id="staff-queue",
            email="staff-queue@example.edu",
            full_name="Queue Staff",
            password="test-password",
            role="maintenance_staff",
            is_staff=True,
        )
        reporter = User.objects.create_user(
            school_id="student-queue",
            email="student-queue@example.edu",
            full_name="Queue Reporter",
            password="test-password",
            role="student",
        )
        building = Building.objects.create(
            building_code="SCI",
            building_name="Science",
            total_floors=3,
        )
        room = Room.objects.create(
            building=building,
            room_name="201",
            floor_number=2,
        )
        RepairRequest.objects.create(
            reporter=reporter,
            room=room,
            title="Available light repair",
            description="A light is out.",
            priority="high",
            status="pending",
        )
        RepairRequest.objects.create(
            reporter=reporter,
            assigned_staff=staff,
            room=room,
            title="Claimed repair",
            description="Already assigned.",
            priority="medium",
            status="in_progress",
        )
        RepairRequest.objects.create(
            reporter=reporter,
            room=room,
            title="Unclaimed in-progress repair",
            description="Active but not yet assigned.",
            priority="medium",
            status="in_progress",
        )
        RepairRequest.objects.create(
            reporter=reporter,
            room=room,
            title="Finished repair",
            description="Already finished.",
            priority="low",
            status="finished",
        )
        self.client.force_login(staff)

        response = self.client.get(reverse("home:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available light repair")
        self.assertContains(response, "Unclaimed in-progress repair")
        self.assertContains(response, "Take Request")
        self.assertNotContains(response, "Claimed repair")
        self.assertNotContains(response, "Finished repair")
