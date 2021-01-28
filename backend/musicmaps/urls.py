from django.urls import path

from . import views

app_name = 'muscimaps'

urlpatterns = [
    path('geo/', views.MusicMapsGeo.as_view()),
    path('', views.MusicMaps.as_view())
]