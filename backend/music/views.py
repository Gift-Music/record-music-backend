import requests
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts import authentication
from backend import settings
from .serializers import *


class MusicView(APIView):
    """
    Basic Music CRUD methods
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = MusicSerializer

    def get(self, request):
        try:
            music = Music.objects.get(id=request.data.get('id'))
        except Music.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MusicSerializer(music)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MusicSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            music = Music.objects.get(id=request.data.get('id'))
        except Music.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MusicSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            music = serializer.update(instance=music, validated_data=serializer.validated_data)

            serializer = MusicSerializer(music)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            music = Music.objects.get(id=request.data.get('id'))
        except Music.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        music.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpotifyMusicSearch(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        import base64
        import requests

        app_id = settings.SPOTIFY_APP_ID
        app_secret = settings.SPOTIFY_APP_SECRET

        client_info = f'{app_id}:{app_secret}'
        encoded_string = client_info.encode('ascii')
        b64encoded = base64.b64encode(encoded_string)

        header = f'Basic {b64encoded.decode()}'

        uri = requests.post('https://accounts.spotify.com/api/token', headers={'Authorization': header},
                            data={'grant_type': 'client_credentials'})

        access_token = uri.json()['access_token']
        header = f'Bearer {access_token}'

        q = request.data.get('q')
        type = request.data.get('type')

        params = {'q': q, 'type': type}

        uri = requests.get('https://api.spotify.com/v1/search', headers={'Authorization': header}, params=params)

        return Response(uri.json())

