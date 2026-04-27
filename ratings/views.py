from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsMotorista

from .serializers import AvaliacaoCreateSerializer, AvaliacaoResponseSerializer


class AvaliacaoCreateView(APIView):
    permission_classes = [IsAuthenticated, IsMotorista]

    def post(self, request, *args, **kwargs):
        serializer = AvaliacaoCreateSerializer(
            data=request.data,
            context={'motorista': request.user.motorista},
        )
        serializer.is_valid(raise_exception=True)
        avaliacao = serializer.save()
        return Response(
            AvaliacaoResponseSerializer(avaliacao).data,
            status=status.HTTP_201_CREATED,
        )
