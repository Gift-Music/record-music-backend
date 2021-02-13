from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import *


class MusicView(APIView):
    """
    Basic Music CRUD methods
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        try:
            music = Music.objects.get(id=request.data.get('id'))
        except Music.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MusicSerializer(data=music)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MusicSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            music = Music.objects.get(id=request.data.get('id'))
        except Music.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = MusicSerializer(data=request.data)
        if serializer.is_valid():
            music = serializer.update(instance=music, validated_data=serializer.validated_data)

            serializer = MusicSerializer(music)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            music = Music.objects.get(id=request.data.get('id'))
        except Music.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        music.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
