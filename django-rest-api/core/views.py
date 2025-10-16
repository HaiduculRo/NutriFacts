import base64
import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .serializers import UserLoginSerializer, UserRegistrationSerializer

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

class LoginView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
            user.is_email_verified = True
            user.save()
            return Response({"message": "Email verified successfully"})
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid verification token"},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            profile = user.profile
            return Response({
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'profile_picture': profile.profile_picture.url if profile.profile_picture else None
            })
        except Exception as e:
            logger.error(f"Error in UserProfileView.get: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            user = request.user
            profile = user.profile

            # Handle profile picture upload
            if 'profile_picture' in request.data:
                image_data = request.data['profile_picture']
                
                # Handle base64 image data
                if isinstance(image_data, str) and image_data.startswith('data:image'):
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    image_data = ContentFile(base64.b64decode(imgstr), name=f'profile.{ext}')
                
                # Save the image
                profile.profile_picture = image_data
                profile.save()

                return Response({
                    'message': 'Profile picture updated successfully',
                    'profile_picture': profile.profile_picture.url
                })
            
            # Handle name updates
            elif 'first_name' in request.data or 'last_name' in request.data:
                if 'first_name' in request.data:
                    user.first_name = request.data['first_name']
                if 'last_name' in request.data:
                    user.last_name = request.data['last_name']
                user.save()

                return Response({
                    'message': 'Profile updated successfully',
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
            else:
                return Response({'error': 'No valid data provided'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in UserProfileView.post: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 