import shutil
import tempfile
from django.contrib.auth import get_user_model
from posts.models import Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        Post.objects.create(
            text='Тестовый текст',
            pub_date='',
            author=User.objects.get(username='TestUser'),
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        count_post = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'image': SimpleUploadedFile(
                    name='image.jpg',
                    content=self.pic,
                    content_type='image/jpg')
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': 'TestUser'
        }))
        self.assertEqual(Post.objects.count(), count_post + 1)

    def test_edit_post(self):
        form_data = {
            'text': 'измененный текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': 1
            }),
            data=form_data,
            follow=True
        )
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': 1
        }))

    def test_new_comment_is_exist_on_post_page(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': 1
            }))
        post = response.context['post']
        count_comment = post.comments.count()
        form_data = {
            'text': 'измененный текст',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': 1
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(post.comments.count(), count_comment + 1)

    def test_comment_only_for_aythorized(self):
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': 1
            }))
        post = response.context['post']
        count_comment = post.comments.count()
        form_data = {
            'text': 'измененный текст',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': 1
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(post.comments.count(), count_comment)
