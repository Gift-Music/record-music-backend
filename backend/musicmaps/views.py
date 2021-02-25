from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import json
from accounts.authentication import CustomJWTAuthentication
from musicmaps.controller import *


class MusicMapsGeo(APIView):
    """
    Get MusicMaps by Coordinates
    """
    authentication_classes = (CustomJWTAuthentication,)

    def get(self, request, format=None):
        body = json.loads(request.body)
        res = get_music_maps_geo(body['coordinates'])
        if res.hits.total.value == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=res.to_dict(), status=status.HTTP_200_OK)


class MusicMaps(APIView):
    """
    Create, Update, Delete MusicMaps
    """
    authentication_classes = (CustomJWTAuthentication,)

    def post(self, request):
        result = create_music_maps(request.data)
        return Response(data=result, status=status.HTTP_200_OK)

    def put(self, request):
        result = update_music_maps(request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=result, status=status.HTTP_200_OK)

    def delete(self, request):
        result = delete_music_maps(request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=result, status=status.HTTP_200_OK)


class Comment(APIView):
    """
        Create, Update, Delete MusicMaps
    """
    authentication_classes = (CustomJWTAuthentication,)

    def post(self, request):
        result = add_comment(request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=result, status=status.HTTP_200_OK)

    def put(self, request):
        result = update_comment(request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        elif result == 403:
            return Response(data=result, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(data=result, status=status.HTTP_200_OK)

    def delete(self, request):
        result = delete_comment(request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        elif result == 403:
            return Response(data=result, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(data=result, status=status.HTTP_200_OK)


class TotalSearch(APIView):
    def get(self, request):
        result = total_search(data=request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=result, status=status.HTTP_200_OK)


class LocationSearch(APIView):
    def get(self, request):
        result = location_search(data=request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=result, status=status.HTTP_200_OK)


class MusicSearch(APIView):
    def get(self, request):
        result = music_search(data=request.data)
        if result == 404:
            return Response(data=result, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(data=result, status=status.HTTP_200_OK)
