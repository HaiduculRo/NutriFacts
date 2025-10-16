from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework import serializers

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password')
    
    def create(self, validated_data):
        # Folosim email-ul ca username
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,  # Folosim email-ul ca username
            email=email,
            password=validated_data['password']
        )
        
        # Send verification email
        verification_url = f"http://localhost:8000/api/verify-email/{user.verification_token}"
        send_mail(
            'Verify your email',
            f'Click here to verify your email: {verification_url}',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True) 