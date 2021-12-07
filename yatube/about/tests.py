from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_as_expected_location(self):
        status_dict = {
            'about:author': HTTPStatus.OK,
            'about:tech': HTTPStatus.OK
        }
        for url, status in status_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url))
                self.assertEqual(response.status_code, status)

    def test_about_pages_uses_correct_template(self):
        template_dict = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html'
        }
        for url, template in template_dict.items():
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url))
                self.assertTemplateUsed(response, template)
