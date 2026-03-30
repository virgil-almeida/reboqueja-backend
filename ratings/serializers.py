from rest_framework import serializers

from services.models import Solicitacao, SolicitacaoStatus

from .models import Avaliacao


class AvaliacaoCreateSerializer(serializers.ModelSerializer):
    solicitacao_id = serializers.PrimaryKeyRelatedField(
        queryset=Solicitacao.objects.all(),
        source='solicitacao',
        write_only=True,
    )

    class Meta:
        model = Avaliacao
        fields = ['solicitacao_id', 'nota', 'comentario']

    def validate(self, attrs):
        solicitacao = attrs['solicitacao']
        motorista = self.context['motorista']
        if solicitacao.motorista_id != motorista.id:
            raise serializers.ValidationError('Esta solicitação não pertence a você.')
        if solicitacao.status != SolicitacaoStatus.CONCLUIDO:
            raise serializers.ValidationError(
                'Só é possível avaliar após o atendimento concluído.',
            )
        if Avaliacao.objects.filter(solicitacao_id=solicitacao.pk).exists():
            raise serializers.ValidationError('Esta solicitação já foi avaliada.')
        if solicitacao.prestador_id is None:
            raise serializers.ValidationError('Solicitação sem prestador vinculado.')
        return attrs

    def create(self, validated_data):
        solicitacao = validated_data.pop('solicitacao')
        return Avaliacao.objects.create(
            solicitacao=solicitacao,
            prestador_id=solicitacao.prestador_id,
            motorista_id=solicitacao.motorista_id,
            **validated_data,
        )


class AvaliacaoResponseSerializer(serializers.ModelSerializer):
    solicitacao_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Avaliacao
        fields = ['id', 'solicitacao_id', 'nota', 'comentario', 'created_at']
