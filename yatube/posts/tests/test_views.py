import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from posts.models import Post, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='TestUser')
        cls.pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')

        Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )

        for i in range(15):
            Post.objects.create(
                text='Тестовый текст' + str(i),
                pub_date='',
                author=User.objects.get(username='TestUser'),
                group=Group.objects.get(title='Тестовая группа'),
                image=SimpleUploadedFile(
                    name='image' + str(i) + '.jpg',
                    content=cls.pic,
                    content_type='image/jpg'
                )
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def context_parse(self, url, kwargs):
        response = self.authorized_client.get(reverse(url, kwargs=kwargs))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        return (
            post_text_0,
            post_author_0,
            post_group_0,
            response,
            post_image_0
        )

    def test_home_page_correct_contextv2(self):
        first_object = self.context_parse('posts:index', '')
        self.assertEqual(first_object[0], 'Тестовый текст14')
        self.assertEqual(first_object[1], self.user)
        self.assertEqual(first_object[2],
                         Group.objects.get(title='Тестовая группа'))
        self.assertEqual(first_object[4].name, 'posts/image14.jpg')

    def test_group_page_correct_context(self):
        first_object = self.context_parse('posts:group', {
            'slug': 'test-slug'
        })
        context_group = first_object[3].context['group']
        self.assertEqual(first_object[0], 'Тестовый текст14')
        self.assertEqual(first_object[1], self.user)
        self.assertEqual(first_object[2],
                         Group.objects.get(title='Тестовая группа'))
        self.assertEqual(context_group,
                         Group.objects.get(title='Тестовая группа'))
        self.assertEqual(first_object[4].name, 'posts/image14.jpg')

    def test_profile_page_correct_context(self):
        first_object = self.context_parse('posts:profile', kwargs={
            'username': 'TestUser'
        })
        context_author = first_object[3].context['author']
        context_count = first_object[3].context['count_post']
        self.assertEqual(first_object[0], 'Тестовый текст14')
        self.assertEqual(first_object[1], self.user)
        self.assertEqual(first_object[2],
                         Group.objects.get(title='Тестовая группа'))
        self.assertEqual(context_author, self.user)
        self.assertEqual(context_count, self.user.posts.all().count())
        self.assertEqual(first_object[4].name, 'posts/image14.jpg')

    def test_post_detail_page_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={
                                                          'post_id': 4
                                                      }))
        context_post = response.context['post']
        context_text = context_post.text
        context_author = context_post.author
        context_group = context_post.group
        context_image = context_post.image
        self.assertEqual(context_text, 'Тестовый текст3')
        self.assertEqual(context_author, self.user)
        self.assertEqual(context_group,
                         Group.objects.get(title='Тестовая группа'))
        self.assertEqual(context_image.name, 'posts/image3.jpg')

    def test_create_post_page_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={
                                                          'post_id': 4
                                                      }))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_used_correct_template(self):
        template_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group', kwargs={
                'slug': 'test-slug'
            }): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'TestUser'
            }): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': '1'
            }): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                'post_id': '1'
            }): 'posts/create_post.html'
        }

        for url, template in template_pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_paginator(self):
        test_url_dict = {
            'posts:index': '',
            'posts:group': {'slug': 'test-slug'},
            'posts:profile': {'username': 'TestUser'}
        }
        for url, values in test_url_dict.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(reverse(url,
                                                              kwargs=values))
                self.assertEqual(len(response.context['page_obj']),
                                 settings.PAGINATE_BY)
                response = self.authorized_client.get(reverse(
                    url, kwargs=values) + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 (Post.objects.all().count() %
                                  settings.PAGINATE_BY))

    def test_new_post_is_exist_on_home_group_profile_pages(self):
        Post.objects.create(
            text='new test post',
            pub_date='',
            author=User.objects.get(username='TestUser'),
            group=Group.objects.get(title='Тестовая группа')
        )

        post_text_dict = {
            'posts:index': '',
            'posts:group': {'slug': 'test-slug'},
            'posts:profile': {'username': 'TestUser'}
        }
        for url, kwargs in post_text_dict.items():
            with self.subTest(url=url):
                first_object = self.context_parse(url, kwargs)
                self.assertEqual(first_object[0], 'new test post')

    def test_new_post_not_exist_on_another_group_pages(self):
        Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Описание тестовой группы2'
        )
        Post.objects.create(
            text='new test post',
            pub_date='',
            author=User.objects.get(username='TestUser'),
            group=Group.objects.get(title='Тестовая группа2')
        )
        response = self.authorized_client.get(reverse('posts:group',
                                                      kwargs={'slug':
                                                              'test-slug2'}))
        first_object = response.context['page_obj'][0]
        response = self.authorized_client.get(reverse('posts:group',
                                                      kwargs={'slug':
                                                              'test-slug'}))
        self.assertNotIn(first_object, response.context['page_obj'])

    def test_index_cache(self):
        test_cache_post = Post.objects.create(
            text='test cache post',
            author=User.objects.get(username='TestUser'))
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotContains(response, test_cache_post)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, test_cache_post)

    def test_follow_unfollow_authorized(self):
        self.user_2 = User.objects.create_user(username='TestUser2')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.assertEqual(count, 0)
        self.authorized_client_2.get(reverse(
            'posts:profile_follow', kwargs={'username': 'TestUser'})
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.assertNotEqual(count, 0)
        self.authorized_client_2.get(reverse(
            'posts:profile_unfollow', kwargs={'username': 'TestUser'})
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        count = len(response.context['page_obj'])
        self.assertEqual(count, 0)

    def test_new_post_is_exist_on_follow_index(self):
        self.user_2 = User.objects.create_user(username='TestUser2')
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.authorized_client_2.get(reverse(
            'posts:profile_follow', kwargs={'username': 'TestUser'})
        )

        Post.objects.create(
            text='test follow post',
            author=User.objects.get(username='TestUser')
        )
        response = self.authorized_client_2.get(reverse('posts:follow_index'))
        context_part = response.context['page_obj'][0]
        post_text = context_part.text
        self.assertEqual(post_text, 'test follow post')
