from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.views import APIView
from .documents import Post
from rest_framework.response import Response
import json
from accounts.authentication import CustomJWTAuthentication


def get_music_maps_geo(coordinates):
    s = Post.search(index='musicmaps').filter({
        'geo_distance': {
            "distance": coordinates.get("distance"),
            "coordinates":
                {"lat": coordinates.get("lat"),
                 "lon": coordinates.get("lon")}
        }
    })
    response = s.execute()
    return response


def create_music_maps(data):
    post = Post(
        open_range=data['open_range'],
        author_id=data['author_id'],
        comments_on=data['comments_on'],
        content=data['content'],
        coordinates=data['coordinates'],
        street_address=data['address'],
        building_number=data['build_num']
    )
    return post.save()


def update_music_maps(data):
    pass


class MusicMapsGeo(APIView):
    """
    Get MusicMaps by Coordinates
    """
    authentication_classes = (CustomJWTAuthentication, )

    def get(self, request, format=None):
        body = json.loads(request.body)
        res = get_music_maps_geo(body['coordinates'])
        if res.hits.total.value == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=res.to_dict(), status=status.HTTP_200_OK)


class MusicMaps(APIView):
    """
    CRUD MusicMaps
    """
    authentication_classes = (CustomJWTAuthentication, )

    def post(self, request):
        result = create_music_maps(request.data)
        return Response(data=result, status=status.HTTP_200_OK)

    def put(self, request):
        result = update_music_maps(request.data)
