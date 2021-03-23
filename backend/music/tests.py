import base64
import tempfile
from unittest import mock

from PIL import Image
from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ImageField
from django.test import TestCase
from rest_framework.test import APIClient

from backend import settings
from .models import *


class ModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        This song's yt_song_id is not a real id.
        """
        cls.data = {
            'artists': 'Sia',
            'name': 'Chandelier',
            'yt_song_id': '34992',
            'cover_image': '...',
        }
        Music.objects.create(artists=cls.data.get('artists'),
                             name=cls.data.get('name'),
                             yt_song_id=cls.data.get('yt_song_id'),
                             cover_image=cls.data.get('cover_image'))

    def test_setUpData_check(self):
        self.assertIsNotNone(Music.objects.all())

        music = Music.objects.get(id=1)

        self.assertEqual('Sia', music.artists)
        self.assertEqual('Chandelier', music.name)
        self.assertEqual('34992', music.yt_song_id)
        self.assertEqual('...', music.cover_image)

    def test_should_make_model(self):
        data = {
            'artists': 'TestArtist',
            'name': 'TestMusicName',
            'yt_song_id': '1',
            'cover_image': '...',
        }

        Music.objects.create(artists=data.get('artists'),
                             name=data.get('name'),
                             yt_song_id=data.get('yt_song_id'),
                             cover_image=data.get('cover_image'))

        self.assertIsNotNone(Music.objects.get(id=2))

        music = Music.objects.get(id=2)

        self.assertEqual('TestArtist', music.artists)
        self.assertEqual('TestMusicName', music.name)
        self.assertEqual('1', music.yt_song_id)
        self.assertEqual('...', music.cover_image)

    def test_spotify_search(self):
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

        uri = requests.get('https://api.spotify.com/v1/search', headers={'Authorization': header}, params={
            'q': 'yummy',
            'type': 'track',
        })

        self.assertIsNotNone(uri.content)
