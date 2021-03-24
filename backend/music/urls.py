from django.conf.urls.static import static
from django.urls import path

from backend import settings
from . import views

app_name = 'music'

urlpatterns = [
    path('', views.MusicView.as_view()),
    path('search/', views.SpotifyMusicSearch.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
