from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import YourModel  # Replace with your actual model

class YourModelTests(APITestCase):
    def setUp(self):
        self.model_instance = YourModel.objects.create(
            # Add fields here
        )

    def test_model_creation(self):
        """Test that the model instance is created successfully."""
        self.assertEqual(YourModel.objects.count(), 1)

    def test_model_retrieval(self):
        """Test that the model instance can be retrieved."""
        response = self.client.get(reverse('yourmodel-detail', args=[self.model_instance.id]))  # Adjust the URL name
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_model_update(self):
        """Test that the model instance can be updated."""
        response = self.client.patch(reverse('yourmodel-detail', args=[self.model_instance.id]), data={
            # Add fields to update
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_model_deletion(self):
        """Test that the model instance can be deleted."""
        response = self.client.delete(reverse('yourmodel-detail', args=[self.model_instance.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(YourModel.objects.count(), 0)