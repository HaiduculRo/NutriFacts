from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .views import (NutritionHistoryView, SaveNutritionDataView, ScanImageView,
                    YourModelViewSet)

router = DefaultRouter()
router.register(r'examples', YourModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('scan-image/', ScanImageView.as_view(), name='scan-image'),
    path('save-nutrition-data/', SaveNutritionDataView.as_view(), name='save-nutrition-data'),
    path('nutrition-history/', NutritionHistoryView.as_view(), name='nutrition-history'),
]
