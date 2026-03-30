from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Prestador
from .permissions import IsPrestador
from .serializers import (
    MotoristaCreateSerializer,
    MotoristaResponseSerializer,
    PrestadorCreateSerializer,
    PrestadorDisponibilidadeSerializer,
    PrestadorPublicoSerializer,
    PrestadorResponseSerializer,
    UserMeSerializer,
)


class MotoristaCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = MotoristaCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = MotoristaResponseSerializer(user).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class PrestadorPublicDetailView(generics.RetrieveAPIView):
    queryset = Prestador.objects.select_related('user')
    permission_classes = [AllowAny]
    serializer_class = PrestadorPublicoSerializer


class PrestadorCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PrestadorCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = PrestadorResponseSerializer(user).data
        headers = self.get_success_headers(data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class UserMeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user


class PrestadorDisponibilidadeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsPrestador]
    serializer_class = PrestadorDisponibilidadeSerializer
    http_method_names = ['patch', 'head', 'options']

    def get_object(self):
        return self.request.user.prestador

    def patch(self, request, *args, **kwargs):
        prestador = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(prestador, serializer.validated_data)
        prestador.refresh_from_db()
        return Response(
            {'disponivel': prestador.disponivel},
            status=status.HTTP_200_OK,
        )
