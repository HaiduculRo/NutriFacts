from rest_framework import serializers

from .models import YourModel


class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = '__all__'  # or specify the fields you want to include, e.g., ['id', 'name', 'description']