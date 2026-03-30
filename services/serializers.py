from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from ratings.stats import prestador_media_e_total
from .models import SOLICITACAO_ATIVA, Solicitacao, SolicitacaoStatus


def prestador_para_motorista(obj: Solicitacao):
    """Dados do prestador só após aceite; US-16 inclui média de avaliações."""
    if obj.status not in (
        SolicitacaoStatus.ACEITO,
        SolicitacaoStatus.A_CAMINHO,
        SolicitacaoStatus.CONCLUIDO,
    ):
        return None
    if not obj.prestador_id:
        return None
    stats = prestador_media_e_total(obj.prestador_id)
    p = obj.prestador
    return {
        'id': p.id,
        'nome': p.user.full_name,
        'telefone': p.user.phone or '',
        'placa': p.placa,
        'modelo_veiculo': p.modelo_veiculo,
        'media_avaliacoes': stats['media_avaliacoes'],
    }


class SolicitacaoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitacao
        fields = ['latitude', 'longitude', 'descricao', 'tipo_veiculo']

    def validate(self, attrs):
        motorista = self.context['motorista']
        if Solicitacao.objects.filter(motorista=motorista, status__in=SOLICITACAO_ATIVA).exists():
            raise serializers.ValidationError(
                'Você já possui uma solicitação ativa. Finalize ou cancele antes de criar outra.',
            )
        return attrs

    def create(self, validated_data):
        validated_data['motorista'] = self.context['motorista']
        validated_data['status'] = SolicitacaoStatus.PENDENTE
        return super().create(validated_data)


class SolicitacaoDetailSerializer(serializers.ModelSerializer):
    prestador = serializers.SerializerMethodField()
    timestamps = serializers.SerializerMethodField()

    class Meta:
        model = Solicitacao
        fields = [
            'id',
            'status',
            'latitude',
            'longitude',
            'descricao',
            'tipo_veiculo',
            'prestador',
            'timestamps',
        ]

    def get_prestador(self, obj):
        return prestador_para_motorista(obj)

    def get_timestamps(self, obj):
        return {
            'criado_em': obj.created_at,
            'aceito_em': obj.accepted_at,
            'a_caminho_em': obj.a_caminho_at,
            'concluido_em': obj.concluded_at,
            'cancelado_em': obj.cancelled_at,
        }


class SolicitacaoAceitaSerializer(serializers.ModelSerializer):
    prestador = serializers.SerializerMethodField()
    timestamps = serializers.SerializerMethodField()

    class Meta:
        model = Solicitacao
        fields = [
            'id',
            'status',
            'latitude',
            'longitude',
            'descricao',
            'tipo_veiculo',
            'prestador',
            'timestamps',
        ]

    def get_prestador(self, obj):
        return prestador_para_motorista(obj)

    def get_timestamps(self, obj):
        return {
            'criado_em': obj.created_at,
            'aceito_em': obj.accepted_at,
            'a_caminho_em': obj.a_caminho_at,
            'concluido_em': obj.concluded_at,
            'cancelado_em': obj.cancelled_at,
        }


class PrestadorAtualizaStatusSerializer(serializers.Serializer):
    """Próximo estado desejado: `a_caminho` (após aceito) ou `concluido` (após a caminho)."""

    status = serializers.ChoiceField(choices=[SolicitacaoStatus.A_CAMINHO, SolicitacaoStatus.CONCLUIDO])


class HistoricoMotoristaSerializer(serializers.ModelSerializer):
    data = serializers.DateTimeField(source='created_at', read_only=True)
    prestador = serializers.SerializerMethodField()
    avaliacao = serializers.SerializerMethodField()

    class Meta:
        model = Solicitacao
        fields = ['id', 'status', 'data', 'prestador', 'avaliacao']

    def get_prestador(self, obj):
        if not obj.prestador_id:
            return None
        p = obj.prestador
        return {'id': p.id, 'nome': p.user.full_name, 'placa': p.placa}

    def get_avaliacao(self, obj):
        try:
            a = obj.avaliacao
        except ObjectDoesNotExist:
            return None
        return {'nota': a.nota, 'comentario': a.comentario or ''}


class HistoricoPrestadorSerializer(serializers.ModelSerializer):
    data = serializers.DateTimeField(source='created_at', read_only=True)
    motorista = serializers.SerializerMethodField()
    avaliacao_recebida = serializers.SerializerMethodField()

    class Meta:
        model = Solicitacao
        fields = ['id', 'status', 'data', 'motorista', 'avaliacao_recebida']

    def get_motorista(self, obj):
        m = obj.motorista
        return {'id': m.id, 'nome': m.user.full_name, 'email': m.user.email}

    def get_avaliacao_recebida(self, obj):
        try:
            a = obj.avaliacao
        except ObjectDoesNotExist:
            return None
        return {'nota': a.nota, 'comentario': a.comentario or ''}
