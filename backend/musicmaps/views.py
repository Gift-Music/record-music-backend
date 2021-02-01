import time

from django.core.mail import EmailMessage
from rest_framework import status
from rest_framework.views import APIView
from .documents import Post
from rest_framework.response import Response
import json
from accounts.authentication import CustomJWTAuthentication
from elasticsearch.exceptions import ConflictError


def get_music_maps_geo(coordinates):
    s = Post.search(index='musicmaps').filter({
        'geo_distance': {
            "distance": coordinates.get("distance"),
            "coordinates":
                {"lat": coordinates.get("lat"),
                 "lon": coordinates.get("lon")}
        }
    })
    return s.execute()


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
    post = Post.get(id=data['id'])
    if post is not None:
        return post.update(
            open_range=data['open_range'],
            comments_on=data['comments_on'],
            content=data['content'],
            coordinates=data['coordinates'],
            street_address=data['address'],
            building_number=data['build_num'],
            retry_on_conflict=5
        )
    else:
        return 404


def delete_music_maps(data):
    post = Post.get(id=data['id'])
    if post is not None:
        try:
            return post.delete()
        except ConflictError:
            time.sleep(1)
            return delete_music_maps(data)
    else:
        return 404


def add_comment(data):
    post = Post.get(id=data['id'])
    if post is not None and post.comments_on:
        try:
            post.add_comment(data['author_id'], data['content'])
            return post.save()
        except ConflictError:
            time.sleep(1)
            return add_comment(data)
    else:
        return 404


def update_comment(data):
    post = Post.get(id=data['id'])
    if post is not None:
        try:
            post.update_comment(data['author_id'], data['content'], data['index'])
            return post.save()
        except ConflictError:
            time.sleep(1)
            return update_comment(data)
    else:
        return 404


def delete_comment(data):
    post = Post.get(id=data['id'])
    if post is not None:
        try:
            post.delete_comment(data['author_id'], data['index'])
            return post.save()
        except ConflictError:
            time.sleep(1)
            return delete_comment(data)
    else:
        return 404


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
