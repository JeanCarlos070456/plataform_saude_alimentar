from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AccessRequest, GalleryItem, PublicationStatus, TeamMember, UserProfile
from .services.gallery import apply_featured_state


class ManagementAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.developer = User.objects.create_user(
            username="dev@example.com",
            email="dev@example.com",
            password="A-secure-test-password-123!",
            is_staff=True,
            is_superuser=True,
        )
        UserProfile.objects.update_or_create(
            user=self.developer,
            defaults={"role": UserProfile.Role.DEVELOPER},
        )

    def test_public_request_access(self):
        response = self.client.post(
            reverse("gestao:request_access"),
            {
                "full_name": "Pessoa Teste",
                "email": "pessoa@example.com",
                "role_description": "Pesquisadora",
            },
        )
        self.assertRedirects(response, reverse("gestao:request_access_done"))
        self.assertTrue(AccessRequest.objects.filter(email="pessoa@example.com").exists())

    def test_manager_dashboard_requires_login(self):
        response = self.client.get(reverse("gestao:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_developer_can_open_dashboard(self):
        self.client.force_login(self.developer)
        response = self.client.get(reverse("gestao:dashboard"))
        self.assertEqual(response.status_code, 200)


class PublicationTests(TestCase):
    def test_publication_status_defaults(self):
        gallery = GalleryItem.objects.create(title="Teste", summary="Resumo")
        member = TeamMember.objects.create(full_name="Pessoa", role="Pesquisadora")
        self.assertEqual(gallery.status, PublicationStatus.PUBLISHED)
        self.assertEqual(member.status, PublicationStatus.PUBLISHED)


class FeaturedGalleryTests(TestCase):
    def _item(self, title):
        return GalleryItem.objects.create(
            title=title,
            summary="Resumo",
            image_url=f"https://example.com/{title}.webp",
            status=PublicationStatus.PUBLISHED,
        )

    def test_featured_gallery_keeps_maximum_of_three(self):
        items = [self._item(f"item-{index}") for index in range(4)]
        for item in items:
            apply_featured_state(item, requested_featured=True)

        featured = list(
            GalleryItem.objects.filter(is_featured=True).order_by("featured_at", "pk")
        )
        self.assertEqual(len(featured), 3)
        self.assertNotIn(items[0].pk, [item.pk for item in featured])
        self.assertIn(items[3].pk, [item.pk for item in featured])

    def test_unfeatured_item_clears_featured_timestamp(self):
        item = self._item("teste")
        apply_featured_state(item, requested_featured=True)
        item.refresh_from_db()
        self.assertTrue(item.is_featured)
        self.assertIsNotNone(item.featured_at)

        apply_featured_state(item, requested_featured=False)
        item.refresh_from_db()
        self.assertFalse(item.is_featured)
        self.assertIsNone(item.featured_at)
