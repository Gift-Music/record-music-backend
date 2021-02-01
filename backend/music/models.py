from django.db import models


class Music(models.Model):
    artists = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    yt_song_id = models.CharField(max_length=30)
    cover_image = models.ImageField(upload_to="../images")
