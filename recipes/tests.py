from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Recipe


class RecipeTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

        self.recipe = Recipe.objects.create(
            name="Arroz con pollo",
            preparation_time=30,
            creator=self.user,   
        )

    def test_recipe_list_status_code(self):
        """La vista de lista de recetas responde 200."""
        url = reverse("recipe_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recipe_name_appears(self):
        """El nombre de la receta aparece en la lista."""
        url = reverse("recipe_list")
        response = self.client.get(url)
        self.assertContains(response, "Arroz con pollo")
