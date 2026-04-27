from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Prestador
from users.permissions import IsMotorista, IsPrestador

from .filters import MotoristaHistoricoFilter
from .geo import calcular_distancia
from .models import Solicitacao, SolicitacaoStatus
from .pagination import HistoricoPagination
from .serializers import (
    HistoricoMotoristaSerializer,
    HistoricoPrestadorSerializer,
    PrestadorAtualizaStatusSerializer,
    SolicitacaoAceitaSerializer,
    SolicitacaoCreateSerializer,
    SolicitacaoDetailSerializer,
)
from .transitions import (
    aplicar_aceite,
    aplicar_cancelamento_motorista,
    aplicar_status_prestador,
)


class SolicitacaoCreateView(APIView):
    permission_classes = [IsAuthenticated, IsMotorista]

    def post(self, request, *args, **kwargs):
        serializer = SolicitacaoCreateSerializer(
            data=request.data,
            context={'motorista': request.user.motorista},
        )
        serializer.is_valid(raise_exception=True)
        solicitacao = serializer.save()
        return Response(
            SolicitacaoDetailSerializer(solicitacao).data,
            status=status.HTTP_201_CREATED,
        )


class SolicitacaoDetailView(APIView):
    permission_classes = [IsAuthenticated, IsMotorista]

    def get(self, request, pk, *args, **kwargs):
        solicitacao = get_object_or_404(
            Solicitacao.objects.select_related('prestador', 'prestador__user'),
            pk=pk,
            motorista=request.user.motorista,
        )
        return Response(SolicitacaoDetailSerializer(solicitacao).data)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='status',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Filtrar por status da solicitação (ex.: concluido, pendente).',
        ),
        OpenApiParameter(
            name='data_inicio',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Data inicial (YYYY-MM-DD), filtra por data de criação.',
        ),
        OpenApiParameter(
            name='data_fim',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Data final (YYYY-MM-DD), filtra por data de criação.',
        ),
    ],
    summary='Histórico de solicitações do motorista',
)
class MotoristaHistoricoListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsMotorista]
    serializer_class = HistoricoMotoristaSerializer
    pagination_class = HistoricoPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = MotoristaHistoricoFilter

    def get_queryset(self):
        return (
            Solicitacao.objects.filter(motorista=self.request.user.motorista)
            .select_related('prestador', 'prestador__user', 'avaliacao')
            .order_by('-created_at')
        )


class PrestadorAtendimentosListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsPrestador]
    serializer_class = HistoricoPrestadorSerializer
    pagination_class = HistoricoPagination

    def get_queryset(self):
        return (
            Solicitacao.objects.filter(prestador=self.request.user.prestador)
            .select_related('motorista', 'motorista__user', 'avaliacao')
            .order_by('-created_at')
        )


class SolicitacaoCancelarView(APIView):
    permission_classes = [IsAuthenticated, IsMotorista]

    def post(self, request, pk, *args, **kwargs):
        with transaction.atomic():
            solicitacao = (
                Solicitacao.objects.select_for_update()
                .filter(pk=pk, motorista=request.user.motorista)
                .first()
            )
            if solicitacao is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            try:
                aplicar_cancelamento_motorista(solicitacao)
            except ValueError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        solicitacao = Solicitacao.objects.select_related('prestador', 'prestador__user').get(pk=pk)
        return Response(SolicitacaoDetailSerializer(solicitacao).data)


class SolicitacaoPrestadorStatusView(APIView):
    permission_classes = [IsAuthenticated, IsPrestador]

    def post(self, request, pk, *args, **kwargs):
        serializer = PrestadorAtualizaStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        novo_status = serializer.validated_data['status']
        prestador = request.user.prestador

        with transaction.atomic():
            solicitacao = Solicitacao.objects.select_for_update().filter(pk=pk).first()
            if solicitacao is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            try:
                aplicar_status_prestador(solicitacao, prestador, novo_status)
            except ValueError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        solicitacao = Solicitacao.objects.select_related('prestador', 'prestador__user').get(pk=pk)
        return Response(SolicitacaoDetailSerializer(solicitacao).data)


class PrestadoresProximosView(APIView):
    """Listagem de prestadores com distância (mesmo algoritmo Haversine que solicitações)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            lat = Decimal(str(request.query_params.get('lat', '')))
            lng = Decimal(str(request.query_params.get('lng', '')))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {'detail': 'Informe lat e lng válidos como parâmetros de consulta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            raio = float(request.query_params.get('raio', '30'))
        except (TypeError, ValueError):
            raio = 30.0
        if raio <= 0:
            return Response(
                {'detail': 'O raio deve ser maior que zero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = []
        qs = Prestador.objects.filter(disponivel=True).select_related('user')
        for p in qs:
            d = calcular_distancia(
                float(lat),
                float(lng),
                float(p.base_latitude),
                float(p.base_longitude),
            )
            if d <= raio:
                items.append(
                    {
                        'id': p.id,
                        'nome': p.user.full_name,
                        'email': p.user.email,
                        'placa': p.placa,
                        'modelo_veiculo': p.modelo_veiculo,
                        'latitude': float(p.base_latitude),
                        'longitude': float(p.base_longitude),
                        'distancia_km': round(d, 3),
                    }
                )
        items.sort(key=lambda x: x['distancia_km'])
        return Response(items)


class SolicitacoesDisponiveisView(APIView):
    permission_classes = [IsAuthenticated, IsPrestador]

    def get(self, request, *args, **kwargs):
        prestador = request.user.prestador
        if not prestador.disponivel:
            return Response([])

        try:
            lat = Decimal(str(request.query_params.get('lat', '')))
            lng = Decimal(str(request.query_params.get('lng', '')))
        except (InvalidOperation, TypeError, ValueError):
            return Response(
                {'detail': 'Informe lat e lng válidos como parâmetros de consulta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            raio = float(request.query_params.get('raio', '30'))
        except (TypeError, ValueError):
            raio = 30.0
        if raio <= 0:
            return Response(
                {'detail': 'O raio deve ser maior que zero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = Solicitacao.objects.filter(status=SolicitacaoStatus.PENDENTE).select_related(
            'motorista',
        )
        items = []
        for s in qs:
            d = calcular_distancia(float(lat), float(lng), float(s.latitude), float(s.longitude))
            if d <= raio:
                items.append(
                    {
                        'id': s.id,
                        'latitude': float(s.latitude),
                        'longitude': float(s.longitude),
                        'descricao': s.descricao,
                        'tipo_veiculo': s.tipo_veiculo,
                        'distancia_km': round(d, 3),
                    }
                )
        items.sort(key=lambda x: x['distancia_km'])
        return Response(items)


class SolicitacaoAceitarView(APIView):
    permission_classes = [IsAuthenticated, IsPrestador]

    def post(self, request, pk, *args, **kwargs):
        prestador = request.user.prestador
        if not prestador.disponivel:
            return Response(
                {'detail': 'Ative sua disponibilidade para aceitar solicitações.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            solicitacao = (
                Solicitacao.objects.select_for_update()
                .select_related('prestador', 'prestador__user')
                .filter(pk=pk)
                .first()
            )
            if solicitacao is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if (
                solicitacao.status == SolicitacaoStatus.ACEITO
                and solicitacao.prestador_id == prestador.id
            ):
                return Response(SolicitacaoAceitaSerializer(solicitacao).data)

            if solicitacao.status != SolicitacaoStatus.PENDENTE or solicitacao.prestador_id is not None:
                return Response(
                    {'detail': 'Esta solicitação já foi aceita por outro prestador.'},
                    status=status.HTTP_409_CONFLICT,
                )

            try:
                aplicar_aceite(solicitacao, prestador)
            except ValueError:  # pragma: no cover
                return Response(
                    {'detail': 'Esta solicitação já foi aceita por outro prestador.'},
                    status=status.HTTP_409_CONFLICT,
                )

        solicitacao = Solicitacao.objects.select_related('prestador', 'prestador__user').get(pk=pk)
        return Response(
            SolicitacaoAceitaSerializer(solicitacao).data,
            status=status.HTTP_200_OK,
        )


class SolicitacaoRecusarView(APIView):
    permission_classes = [IsAuthenticated, IsPrestador]

    def post(self, request, pk, *args, **kwargs):
        if not Solicitacao.objects.filter(pk=pk).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
