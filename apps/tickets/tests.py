from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

from apps.home.models import (
	Building,
	Notification,
	RepairRequest,
	RequestComment,
	RequestPhoto,
	Room,
	User,
)
from apps.tickets.views import active_reporters_queryset


class TicketWorkflowTests(TestCase):
	def issue_photo(self, name="issue.jpg"):
		stream = BytesIO()
		Image.new("RGB", (20, 20), "white").save(stream, format="JPEG")
		return SimpleUploadedFile(name, stream.getvalue(), content_type="image/jpeg")

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
			role="maintenance_staff",
			is_staff=True,
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
	def test_primary_navigation_is_available_from_profile(self):
		self.client.force_login(self.reporter)

		response = self.client.get(reverse("profile:profile"))

		self.assertEqual(response.status_code, 200)
		for route_name in (
			"home:home",
			"tickets:ticket_list",
			"tickets:ticket_create",
			"tickets:notifications",
			"profile:profile",
			"user_settings:settings",
		):
			self.assertContains(response, f'href="{reverse(route_name)}"')
		self.assertContains(response, 'aria-current="page"')
		self.assertNotContains(response, f'href="{reverse("tickets:active_reporters")}"')

	def test_active_reporters_report_uses_subquery_and_shows_matching_users(self):
		for title, status in (
			("Pending issue", "pending"),
			("In progress issue", "in_progress"),
		):
			RepairRequest.objects.create(
				reporter=self.reporter,
				room=self.room,
				title=title,
				description="Issue details",
				priority="medium",
				status=status,
			)
		RepairRequest.objects.create(
			reporter=self.other_reporter,
			room=self.room,
			title="Closed issue",
			description="Issue details",
			priority="medium",
			status="finished",
		)

		self.assertIn("IN (SELECT", str(active_reporters_queryset().query).upper())
		self.client.force_login(self.staff)
		response = self.client.get(reverse("tickets:active_reporters"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, f"<td>{self.reporter.school_id}</td>", html=True)
		self.assertContains(response, "<td>2</td>", html=True)
		self.assertNotContains(response, self.other_reporter.school_id)
		self.assertContains(response, "Reports")

	def test_reporter_cannot_access_active_reporters_report(self):
		self.client.force_login(self.reporter)

		response = self.client.get(reverse("tickets:active_reporters"))

		self.assertRedirects(response, reverse("tickets:ticket_list"))

	def test_create_rejects_room_from_another_building(self):
		self.client.force_login(self.reporter)

		response = self.client.post(reverse("tickets:ticket_create"), {
			"title": "Broken light",
			"description": "The room light is out.",
			"priority": "medium",
			"building_id": self.other_building.pk,
			"room_id": self.room.pk,
			"photos": [self.issue_photo()],
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
			"room_id": self.room.pk,
			"photos": [self.issue_photo()],
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
			"building_id": self.building.pk,
			"room_id": self.room.pk,
			"photos": [self.issue_photo()],
		})

		ticket = RepairRequest.objects.get()
		self.assertRedirects(
			response,
			reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}),
		)
		self.assertEqual(ticket.status_history.count(), 1)
		self.assertEqual(ticket.status_history.get().new_status, "pending")
		self.assertTrue(ticket.photos.filter(photo_type="issue").exists())

	def test_create_rejects_more_than_five_issue_photos(self):
		self.client.force_login(self.reporter)

		response = self.client.post(reverse("tickets:ticket_create"), {
			"title": "Broken light",
			"description": "The room light is out.",
			"priority": "medium",
			"building_id": self.building.pk,
			"room_id": self.room.pk,
			"photos": [self.issue_photo(f"issue-{index}.jpg") for index in range(6)],
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "You can upload up to 5 photos.")
		self.assertEqual(RepairRequest.objects.count(), 0)

	def test_ticket_list_renders_status_label(self):
		RepairRequest.objects.create(
			reporter=self.reporter,
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
		self.assertContains(response, f"{self.building.building_name} / {self.room.room_name}")
		self.assertNotContains(response, "Category")

	def test_maintenance_staff_ticket_list_shows_only_unclaimed_pending_requests(self):
		RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Available repair",
			description="Waiting for maintenance.",
			priority="high",
			status="pending",
		)
		RepairRequest.objects.create(
			reporter=self.other_reporter,
			assigned_staff=self.staff,
			room=self.room,
			title="Claimed repair",
			description="Already assigned.",
			priority="medium",
			status="in_progress",
		)
		RepairRequest.objects.create(
			reporter=self.other_reporter,
			room=self.room,
			title="Unclaimed in-progress repair",
			description="Active but not yet assigned.",
			priority="medium",
			status="in_progress",
		)
		RepairRequest.objects.create(
			reporter=self.other_reporter,
			room=self.room,
			title="Finished repair",
			description="Already finished.",
			priority="low",
			status="finished",
		)
		self.client.force_login(self.staff)

		response = self.client.get(reverse("tickets:ticket_list"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Available repair")
		self.assertContains(response, "Unclaimed in-progress repair")
		self.assertContains(response, "Take Request")
		self.assertContains(response, self.reporter.full_name)
		self.assertNotContains(response, "Claimed repair")
		self.assertNotContains(response, "Finished repair")

	def test_reporter_comment_notifies_staff_when_ticket_is_unassigned(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Unassigned ticket",
			description="Issue details",
			priority="medium",
			status="pending",
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
			room=self.room,
			title="Private ticket",
			description="Issue details",
			priority="medium",
			status="pending",
		)
		self.client.force_login(self.reporter)

		response = self.client.post(
			reverse("tickets:post_comment", kwargs={"pk": ticket.request_id}),
			{"body": "Unauthorized comment"},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response["Location"], reverse("tickets:ticket_list"))
		self.assertEqual(RequestComment.objects.count(), 0)

	def test_maintenance_staff_can_take_pending_ticket(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Pending repair",
			description="Issue details",
			priority="medium",
			status="pending",
		)
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse("tickets:take_ticket", kwargs={"pk": ticket.request_id})
		)

		ticket.refresh_from_db()
		self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}))
		self.assertEqual(ticket.assigned_staff, self.staff)
		self.assertEqual(ticket.status, "in_progress")

	def test_maintenance_staff_cannot_take_a_request_that_is_not_pending_and_unassigned(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Finished repair",
			description="Already finished.",
			priority="medium",
			status="finished",
		)
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse("tickets:take_ticket", kwargs={"pk": ticket.request_id})
		)

		ticket.refresh_from_db()
		self.assertRedirects(
			response,
			reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}),
		)
		self.assertIsNone(ticket.assigned_staff)
		self.assertEqual(ticket.status, "finished")

	def test_maintenance_staff_can_take_an_unassigned_in_progress_request(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Unassigned active repair",
			description="Active, but no staff member has taken it.",
			priority="medium",
			status="in_progress",
		)
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse("tickets:take_ticket", kwargs={"pk": ticket.request_id})
		)

		ticket.refresh_from_db()
		self.assertRedirects(
			response,
			reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}),
		)
		self.assertEqual(ticket.assigned_staff, self.staff)
		self.assertEqual(ticket.status, "in_progress")
		self.assertEqual(
			ticket.status_history.latest("changed_at").old_status,
			"in_progress",
		)

	def test_finished_status_requires_proof_photo(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Repair to finish",
			description="Issue details",
			priority="medium",
			status="in_progress",
			assigned_staff=self.staff,
		)
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse("tickets:update_status", kwargs={"pk": ticket.request_id}),
			{"new_status": "finished", "assigned_staff_id": str(self.staff.user_id)},
			follow=True,
		)

		ticket.refresh_from_db()
		self.assertEqual(ticket.status, "in_progress")
		self.assertContains(response, "At least one proof photo is required")

	def test_finished_status_accepts_up_to_five_proof_photos(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Repair completed",
			description="Issue details",
			priority="medium",
			status="in_progress",
			assigned_staff=self.staff,
		)
		for index in range(3):
			RequestPhoto.objects.create(
				request=ticket,
				photo_url=f"/media/proof_photos/existing-{index}.jpg",
				photo_type="proof",
			)
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse("tickets:update_status", kwargs={"pk": ticket.request_id}),
			{
				"new_status": "finished",
				"assigned_staff_id": str(self.staff.user_id),
				"proof_photos": [self.issue_photo("proof-1.jpg"), self.issue_photo("proof-2.jpg")],
			},
		)

		ticket.refresh_from_db()
		self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}))
		self.assertEqual(ticket.status, "finished")
		self.assertEqual(ticket.photos.filter(photo_type="proof").count(), 5)

	def test_proof_upload_rejects_files_that_exceed_the_total_photo_limit(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Repair in progress",
			description="Issue details",
			priority="medium",
			status="in_progress",
			assigned_staff=self.staff,
		)
		for index in range(4):
			RequestPhoto.objects.create(
				request=ticket,
				photo_url=f"/media/proof_photos/existing-{index}.jpg",
				photo_type="proof",
			)
		self.client.force_login(self.staff)

		response = self.client.post(
			reverse("tickets:update_status", kwargs={"pk": ticket.request_id}),
			{
				"new_status": "in_progress",
				"proof_photos": [
					self.issue_photo("proof-new-1.jpg"),
					self.issue_photo("proof-new-2.jpg"),
				],
			},
			follow=True,
		)

		ticket.refresh_from_db()
		self.assertContains(response, "A ticket can have no more than 5 proof photos.")
		self.assertEqual(ticket.status, "in_progress")
		self.assertEqual(ticket.photos.filter(photo_type="proof").count(), 4)

	def test_reporter_can_edit_unassigned_pending_ticket(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Original title",
			description="Original details",
			priority="medium",
			status="pending",
		)
		self.client.force_login(self.reporter)

		response = self.client.post(
			reverse("tickets:edit_ticket", kwargs={"pk": ticket.request_id}),
			{
				"title": "Updated title",
				"description": "Updated details",
				"priority": "high",
				"building_id": str(self.building.building_id),
				"room_id": str(self.room.room_id),
			},
		)

		ticket.refresh_from_db()
		self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}))
		self.assertEqual(ticket.title, "Updated title")
		self.assertEqual(ticket.description, "Updated details")
		self.assertEqual(ticket.priority, "high")

	def test_editing_ticket_appends_issue_photos_without_replacing_existing_photos(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			room=self.room,
			title="Original title",
			description="Original details",
			priority="medium",
			status="pending",
		)
		RequestPhoto.objects.create(
			request=ticket,
			photo_url="/media/request_photos/existing.jpg",
			photo_type="issue",
		)
		self.client.force_login(self.reporter)
		edit_url = reverse("tickets:edit_ticket", kwargs={"pk": ticket.request_id})

		edit_response = self.client.get(edit_url)

		self.assertEqual(edit_response.status_code, 200)
		self.assertContains(edit_response, "Saved issue photos are kept.")
		self.assertContains(edit_response, 'data-photo-existing="1"')

		response = self.client.post(
			edit_url,
			{
				"title": "Updated title",
				"description": "Updated details",
				"priority": "high",
				"building_id": str(self.building.building_id),
				"room_id": str(self.room.room_id),
				"photos": [self.issue_photo("new-issue.jpg")],
			},
		)

		self.assertRedirects(
			response,
			reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}),
		)
		self.assertEqual(ticket.photos.filter(photo_type="issue").count(), 2)

	def test_reporter_cannot_edit_ticket_after_maintenance_staff_takes_it(self):
		ticket = RepairRequest.objects.create(
			reporter=self.reporter,
			assigned_staff=self.staff,
			room=self.room,
			title="Assigned repair",
			description="Issue details",
			priority="medium",
			status="in_progress",
		)
		self.client.force_login(self.reporter)

		response = self.client.post(
			reverse("tickets:edit_ticket", kwargs={"pk": ticket.request_id}),
			{
				"title": "Changed title",
				"description": "Changed details",
				"priority": "low",
				"building_id": str(self.building.building_id),
				"room_id": str(self.room.room_id),
			},
		)

		ticket.refresh_from_db()
		self.assertRedirects(response, reverse("tickets:ticket_detail", kwargs={"pk": ticket.request_id}))
		self.assertEqual(ticket.title, "Assigned repair")
