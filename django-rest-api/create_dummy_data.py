import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import NutritionHistory, Product
from django.contrib.auth.models import User


def create_dummy_data():
    # Creăm un produs dummy
    product = Product.objects.create(
        product_name='Test Product',
        brand='Test Brand',
        category='Test Category',
        nutri_score='A'
    )
    print(f"Produs dummy creat: {product.product_name}")

    # Obținem un user existent (sau folosim primul user din baza de date)
    user = User.objects.first()
    if not user:
        print("Nu există niciun user în baza de date. Creează un user mai întâi.")
        return

    # Creăm o înregistrare dummy în istoricul nutrițional
    nutrition_history = NutritionHistory.objects.create(
        user=user,
        product=product,
        fat_100g=2.0,
        saturated_fat_100g=1.0,
        trans_fat_100g=0.0,
        cholesterol_100g=0.0,
        sodium_100g=100.0,
        carbohydrates_100g=20.0,
        fiber_100g=2.0,
        sugars_100g=5.0,
        proteins_100g=5.0,
        nutri_score='A'
    )
    print(f"Înregistrare dummy în istoricul nutrițional creată pentru: {product.product_name}")

if __name__ == '__main__':
    create_dummy_data()