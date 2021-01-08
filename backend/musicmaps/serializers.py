from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from django.conf import settings
from . import models


class MusicMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MusicMaps
        fields = (
            '_id',
            'images',
            'playlist',
            'author'
        )
