from django.test import TestCase
from django.urls import reverse

from apps.home.models import (
	Building,
	Category,
	Notification,
	RepairRequest,
	RequestComment,
	Room,
	User,
)


class TicketWorkflowTests(TestCase):
	def setUp(self):
		self.reporter = User.objects.create_user(
			school_id="student-1",
			email="student@example.edu",
			full_name="Test Student",
			password="test-password",
			role="student",
		)
		self.other_reporter = User.objects.create_user(
			school_id="student-2",
			email="other@example.edu",
			full_name="Other Student",
			password="test-password",
			role="student",
		)
		self.staff = User.objects.create_user(
			school_id="staff-1",
			email="staff@example.edu",
			full_name="Test Staff",
			password="test-password",
			role="staff",
		)
		self.building = Building.objects.create(
			building_code="ENG",
			building_name="Engineering",
			total_floors=4,
		)
		self.other_building = Building.objects.create(
			building_code="LIB",
			building_name="Library",
			total_floors=3,
		)
		self.room = Room.objects.create(
			building=self.building,
			room_name="101",
			floor_number=1,
		)
		self.category = Category.objects.create(category_name="Electrical")

	def test_create_rejects_room_from_another_building(self):
		self.client.force_login(self.reporter)

		response = self.client.post(reverse("tickets:ticket_create"), {
			"title": "Broken light",
			"description": "The room light is out.",
			"priority": "medium",
			"category_id": self.category.pk,
			"building_id": self.other_building.pk,
			"room_id": self.room.pk,
		})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(RepairRequest.objects.count(), 0)
		self.assertContains(response, "does not belong to that building")

	def test_create_requires_building_even_when_room_is_provided(self):
		self.client.force_login(self.reporter)

		response = self.client.post(reverse("tickets:ticket_create"), {
			"title": "Broken light",
			"description": "The room light is out.",
			"priority": "medium",
			"category_id": self.category.pk,
			"room_id": self.room.pk,
		})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(RepairRequest.objects.count(), 0)
		self.assertContains(response, "Please select a building and room.")

	def test_create_records_initial_status_history(self):
		self.client.force_login(self.reporter)

		response = self.client.post(reverse("tickets:ticket_create"), {
			"title": "Broken light",
			"description": "The room light is out.",
			"priority": "medium",
			"category_id": self.category.pk,
			"building_id": self.building.pk,
			"room_id": self.room.pk,
		})

		ticket = RepairRequest.objects.get()
		self.assertRedirects(
			response,
			reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}),
		)
		self.assertEqual(ticket.status_history.count(), 1)
		self.assertEqual(ticket.status_history.get().new_status, "open")

	def test_ticket_list_renders_status_label(self):
		RepairRequest.objects.create(
			reporter=self.reporter,
			category=self.category,
			room=self.room,
			title="Work in progress",
			description="Issue details",
			priority="medium",
			status="in_progress",
		)
		self.client.force_login(self.reporter)

		response = self.client.get(reverse("tickets:ticket_list"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "In Progress")

	def test_reporter_comment_notifies_staff_when_ticket_is_unassigned(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			category=self.category,
			room=self.room,
			title="Unassigned ticket",
			description="Issue details",
			priority="medium",
			status="open",
		)
		self.client.force_login(self.reporter)

		response = self.client.post(
			reverse("tickets:post_comment", kwargs={"pk": ticket.request_id}),
			{"body": "Adding more details"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(RequestComment.objects.filter(request=ticket).count(), 1)
		self.assertTrue(Notification.objects.filter(user=self.staff, request=ticket).exists())

	def test_reporter_cannot_comment_on_another_users_ticket(self):
		ticket = RepairRequest.objects.create(
			reporter=self.other_reporter,
			category=self.category,
			room=self.room,
			title="Private ticket",
			description="Issue details",
			priority="medium",
			status="open",
		)
		self.client.force_login(self.reporter)

		response = self.client.post(
			reverse("tickets:post_comment", kwargs={"pk": ticket.request_id}),
			{"body": "Unauthorized comment"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], reverse("tickets:ticket_list"))
		self.assertEqual(RequestComment.objects.count(), 0)
