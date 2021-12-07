from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Post, Group

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='TestUser')
        # Создадим запись в БД для проверки доступности адреса task/test-slug/

        Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )

        Post.objects.create(
            text='Тестовый текст',
            pub_date='',
            author=User.objects.get(username='TestUser'),
            group=Group.objects.get(title='Тестовая группа')
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_at_expected_location(self):
        address_dict_guest = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/TestUser/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/posts/not_exist': HTTPStatus.NOT_FOUND,
            '/create/': HTTPStatus.FOUND,
            '/posts/1/edit/': HTTPStatus.FOUND

        }
        address_dict_autorized = {
            '/create/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK
        }
        for address, status in address_dict_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)
        for address, status in address_dict_autorized.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_redirect_guest_editor(self):
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}))
        self.assertRedirects(response,
                             (reverse('users:login')
                              + '?next='
                              + reverse('posts:post_edit',
                              kwargs={'post_id': 1})))

    def test_urls_correct_templates(self):
        templates_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/TestUser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html'
        }
        for address, template in templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
