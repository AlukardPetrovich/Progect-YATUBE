from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Первые 15 символов должны выводиться при обращении',
        )

    def test_model_group_have_correct_object_name(self):
        """Проверяем, что у модели group корректно работает __str__."""
        group = PostModelTest.group
        expected = group.title
        self.assertEqual(expected, str(group))

    def test_model_post__have_correct_object_name(self):
        """Проверяем, что у модели post корректно работает __str__."""
        post = PostModelTest.post
        expected = post.text[:15]
        self.assertEqual(expected, str(post))

    def test_models_verbose_name(self):
        group = PostModelTest.group
        group_fields = {
            'title': 'Название группы',
            'slug': 'адрес группы',
            'description': 'Подробное описание группы'
        }
        for field, expected_value in group_fields.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value
                )
        post = PostModelTest.post
        post_fields = {
            'author': 'Автор',
            'text': 'Текст поста'
        }

        for field, expected_value in post_fields.items():
            with self.subTest(post=post):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )
