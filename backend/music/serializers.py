from rest_framework import serializers
from .models import *


class MusicSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        if validated_data.get('artists'):
            instance.artists = validated_data.get('artists')
        if validated_data.get('name'):
            instance.name = validated_data.get('name')
        if validated_data.get('yt_song_id'):
            instance.yt_song_id = validated_data.get('yt_song_id')
        if validated_data.get('cover_image'):
            instance.cover_image = validated_data.get('cover_image')
        instance.save()

        return instance

    class Meta:
        model = Music
        fields = '__all__'
