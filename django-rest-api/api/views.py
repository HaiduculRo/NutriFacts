import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add the Django project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

import cv2
import numpy as np
import pytesseract
from core.models import NutritionHistory, Product
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import YourModel
from .serializers import YourModelSerializer

# Configurare logger
logger = logging.getLogger(__name__)

User = get_user_model()

# Configure Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Ensure required files are in place
def setup_scanner_files():
    try:
        # Create necessary directories
        scanner_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scanner')
        os.makedirs(os.path.join(scanner_path, 'tesseract_finetune/tesstrain/data'), exist_ok=True)
        
        # Copy required files if they don't exist
        required_files = {
            'best.pt': os.path.join(scanner_path, 'best.pt'),
            'nuttrition1000.traineddata': os.path.join(scanner_path, 'tesseract_finetune/tesstrain/data/nuttrition1000.traineddata')
        }
        
        for file_name, target_path in required_files.items():
            if not os.path.exists(target_path):
                source_path = os.path.join(scanner_path, file_name)
                if os.path.exists(source_path):
                    shutil.copy2(source_path, target_path)
                    logger.info(f"Copied {file_name} to {target_path}")
                else:
                    logger.error(f"Required file {file_name} not found in scanner directory")
                    return False
        return True
    except Exception as e:
        logger.error(f"Error setting up scanner files: {str(e)}")
        return False

# Setup scanner files
if not setup_scanner_files():
    logger.error("Failed to setup scanner files")

# Import the scanner code after setting up the environment
from scanner.local import detect_and_ocr_with_warp

# No need to override the model path anymore since we fixed it in run_code.py

class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'message': 'Email și parola sunt obligatorii'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if User.objects.filter(email=email).exists():
            return Response(
                {'message': 'Acest email este deja înregistrat'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        
        return Response(
            {'message': 'Cont creat cu succes!'},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            {'message': 'A apărut o eroare la crearea contului'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    logger.info("Login attempt received")  # Print direct în consolă
    email = request.data.get('email')
    password = request.data.get('password')

    logger.info(f"Attempting login for email: {email}")  # Print direct în consolă

    if not email or not password:
        logger.info("Login failed - Missing email or password")  # Print direct în consolă
        return Response(
            {"message": "Email și parola sunt obligatorii"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            # Generăm token-urile JWT
            refresh = RefreshToken.for_user(user)
            
            # Printăm informațiile în consolă
            print(f"Login successful - User ID: {user.id}, Email: {user.email}")
            print(f"Access Token: {str(refresh.access_token)}")
            print(f"Refresh Token: {str(refresh)}")
            
            return Response({
                "message": "Autentificare reușită",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email
                }
            }, status=status.HTTP_200_OK)
        else:
            print(f"Login failed - Invalid password for email: {email}")  # Print direct în consolă
            return Response(
                {"message": "Credențiale invalide"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except User.DoesNotExist:
        print(f"Login failed - User not found with email: {email}")  # Print direct în consolă
        return Response(
            {"message": "Credențiale invalide"},
            status=status.HTTP_401_UNAUTHORIZED
        )

class ScanImageView(APIView):
    permission_classes = [IsAuthenticated]  # Adăugăm autentificare
    
    def post(self, request):
        if 'image' not in request.FILES:
            return Response({
                'error': 'No image provided',
                'message': 'Please provide an image file'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Log user information
            logger.info(f"User attempting to scan image: {request.user.username} (ID: {request.user.id})")
            
            # Save the uploaded image to a temporary file
            image_file = request.FILES['image']
            logger.info(f"Received image: {image_file.name}, size: {image_file.size} bytes")
            
            # Create a temporary file with the correct extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(image_file.read())
            temp_file.close()

            logger.info(f"Processing image: {temp_file.name}")
            
            # Process the image using the scanner code
            try:
                results = detect_and_ocr_with_warp(temp_file.name)
            except Exception as e:
                logger.error(f"Error during image processing: {str(e)}")
                return Response({
                    'error': 'Error processing image',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file.name)
                    logger.info("Temporary file deleted successfully")
                except Exception as e:
                    logger.warning(f"Error deleting temporary file: {str(e)}")

            if not results:
                return Response({
                    'error': 'No nutritional information detected',
                    'message': 'The image was processed but no nutritional information was found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Return the structured data
            return Response({
                'success': True,
                'data': results
            })

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return Response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SaveNutritionDataView(APIView):
    permission_classes = [IsAuthenticated]  # Doar utilizatorii autentificați pot salva date
    
    def post(self, request):
        try:
            # Extract data from request
            data = request.data
            
            # Log user information
            logger.info(f"User attempting to save data: {request.user.username} (ID: {request.user.id})")
            
            # Create or get the product
            product, created = Product.objects.get_or_create(
                product_name=data.get('product_name', 'Unknown Product'),
                brand=data.get('brand', 'Unknown Brand'),
                category=data.get('category', 'Other'),
                nutri_score=data.get('nutri_score', 'E')
            )
            
            # Create nutrition history entry
            try:
                nutrition_history = NutritionHistory.objects.create(
                    user=request.user,  # Setăm direct user-ul autentificat
                    product=product,
                    fat_100g=data.get('fat_100g', 0),
                    saturated_fat_100g=data.get('saturated-fat_100g', 0),
                    trans_fat_100g=data.get('trans-fat_100g', 0),
                    cholesterol_100g=data.get('cholesterol_100g', 0),
                    sodium_100g=data.get('sodium_100g', 0),
                    carbohydrates_100g=data.get('carbohydrates_100g', 0),
                    fiber_100g=data.get('fiber_100g', 0),
                    sugars_100g=data.get('sugars_100g', 0),
                    proteins_100g=data.get('proteins_100g', 0),
                    nutri_score=data.get('nutri_score', 'E'),
                    portion_size=data.get('portion_size', None),
                    image_url=data.get('image_url', None)
                )
                logger.info(f"Successfully created NutritionHistory entry with ID: {nutrition_history.id} for user: {request.user.username}")
                
            except Exception as e:
                logger.error(f"Error creating NutritionHistory entry: {str(e)}")
                return Response({
                    'error': 'Failed to create nutrition history entry',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'message': 'Nutritional data saved successfully',
                'data': {
                    'product_id': str(product.id),
                    'nutrition_history_id': str(nutrition_history.id),
                    'user_id': str(request.user.id)
                }
            })
            
        except Exception as e:
            logger.error(f"Error saving nutritional data: {str(e)}")
            return Response({
                'error': 'Failed to save nutritional data',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NutritionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            logger.info(f"Fetching nutrition history for user: {request.user.username} (ID: {request.user.id})")
            
            # Get the user's nutrition history
            history = NutritionHistory.objects.filter(user=request.user).order_by('-scan_date')
            logger.info(f"Found {history.count()} history entries")
            
            # Serialize the data
            history_data = []
            for item in history:
                try:
                    history_data.append({
                        'id': str(item.id),
                        'product_name': item.product.product_name,
                        'scan_date': item.scan_date,
                        'nutri_score': item.nutri_score,
                        'calories': item.calories if hasattr(item, 'calories') else 0,
                        'protein': float(item.protein) if hasattr(item, 'protein') else 0,
                        'carbs': float(item.carbs) if hasattr(item, 'carbs') else 0,
                        'fat': float(item.fat) if hasattr(item, 'fat') else 0,
                        'fat_100g': float(item.fat_100g) if hasattr(item, 'fat_100g') else 0,
                        'saturated_fat_100g': float(item.saturated_fat_100g) if hasattr(item, 'saturated_fat_100g') else 0,
                        'trans_fat_100g': float(item.trans_fat_100g) if hasattr(item, 'trans_fat_100g') else 0,
                        'cholesterol_100g': float(item.cholesterol_100g) if hasattr(item, 'cholesterol_100g') else 0,
                        'sodium_100g': float(item.sodium_100g) if hasattr(item, 'sodium_100g') else 0,
                        'carbohydrates_100g': float(item.carbohydrates_100g) if hasattr(item, 'carbohydrates_100g') else 0,
                        'fiber_100g': float(item.fiber_100g) if hasattr(item, 'fiber_100g') else 0,
                        'sugars_100g': float(item.sugars_100g) if hasattr(item, 'sugars_100g') else 0,
                        'proteins_100g': float(item.proteins_100g) if hasattr(item, 'proteins_100g') else 0,
                    })
                except Exception as item_error:
                    logger.error(f"Error processing history item {item.id}: {str(item_error)}")
                    continue
            
            logger.info(f"Successfully serialized {len(history_data)} history entries")
            return Response(history_data)
            
        except Exception as e:
            logger.error(f"Error in NutritionHistoryView: {str(e)}")
            return Response({
                'error': 'Failed to fetch nutrition history',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
