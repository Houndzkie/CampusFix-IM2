from django.test import TestCase
from django.urls import reverse


class AuthenticationPageTests(TestCase):
    def test_new_ticket_button_is_hidden_from_anonymous_users(self):
        create_url = reverse("tickets:ticket_create")

        for url in (reverse("login:login"), reverse("register:register")):
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, f'href="{create_url}"')
