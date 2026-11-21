from django.test import TestCase
from django.urls import reverse

from apps.home.models import RepairRequest, Room, Building, User, UserProfile


class ProfileTests(TestCase):
	def setUp(self):
		self.reporter = User.objects.create_user(
			school_id="reporter-profile",
			email="reporter@example.edu",
			full_name="Reporter User",
			password="test-password",
			role="student",
		)
		self.staff = User.objects.create_user(
			school_id="staff-profile",
			email="staff-profile@example.edu",
			full_name="Maintenance User",
			password="test-password",
			role="maintenance_staff",
			is_staff=True,
		)
		UserProfile.objects.create(user=self.reporter, contact_number="09170000001")
		UserProfile.objects.create(user=self.staff, contact_number="09170000002")
		self.building, _ = Building.objects.get_or_create(
			building_code="RTL",
			defaults={"building_name": "RTL", "total_floors": 4},
		)
		self.room, _ = Room.objects.get_or_create(
			building=self.building,
			room_name="101",
			defaults={"floor_number": 1},
		)

	def test_student_profile_shows_report_and_resolved_counts(self):
		RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Resolved issue",
			description="Details",
			priority="medium",
			status="finished",
		)
		self.client.force_login(self.reporter)

		response = self.client.get(reverse("profile:profile"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Reported Requests")
		self.assertContains(response, "Successfully Resolved")
		self.assertContains(response, "09170000001")

	def test_public_profile_is_visible_and_shows_contact_number(self):
		self.client.force_login(self.reporter)

		response = self.client.get(
			reverse("profile:public_profile", kwargs={"user_id": self.staff.user_id})
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "09170000002")
		self.assertContains(response, "Maintenance User")
