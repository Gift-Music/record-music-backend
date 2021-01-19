from django.urls import path

from . import views

app_name = 'muscimaps'

urlpatterns = [
    path('', views.MusicMapsGeo.as_view())
]