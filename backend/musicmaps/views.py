from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.views import APIView
from .documents import Post
from rest_framework.response import Response
import json


def get_music_maps(coordinates):
    s = Post.search(index='musicmaps').filter({
        'geo_distance': {
            "distance": "1km",
            "coordinates":
                {"lat": coordinates.get("lat"),
                 "lon": coordinates.get("lon")}
        }
    })
    response = s.execute()
    return response


class MusicMapsGeo(APIView):
    """
    Get MusicMaps by Coordinates
    """

    def get(self, request, format=None):
        body = json.loads(request.body)
        res = get_music_maps(body['coordinates'])
        if res.hits.total.value == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=res, status=status.HTTP_200_OK)