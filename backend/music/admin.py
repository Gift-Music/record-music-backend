from django.contrib import admin
from .models import *


class MusicAdmin(admin.ModelAdmin):
    list_display = ('name', 'artists', 'yt_song_id', 'cover_image',)


admin.site.register(Music, MusicAdmin)
