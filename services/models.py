from django.db import models
from django.utils.translation import gettext_lazy as _


class SolicitacaoStatus(models.TextChoices):
    PENDENTE = 'pendente', _('Pendente')
    ACEITO = 'aceito', _('Aceito')
    A_CAMINHO = 'a_caminho', _('A caminho')
    CONCLUIDO = 'concluido', _('Concluído')
    CANCELADO = 'cancelado', _('Cancelado')


SOLICITACAO_ATIVA = (
    SolicitacaoStatus.PENDENTE,
    SolicitacaoStatus.ACEITO,
    SolicitacaoStatus.A_CAMINHO,
)


class Solicitacao(models.Model):
    motorista = models.ForeignKey(
        'users.Motorista',
        on_delete=models.CASCADE,
        related_name='solicitacoes',
        verbose_name=_('motorista'),
    )
    prestador = models.ForeignKey(
        'users.Prestador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_atendidas',
        verbose_name=_('prestador'),
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    descricao = models.TextField(_('descrição'))
    tipo_veiculo = models.CharField(_('tipo de veículo'), max_length=100)
    status = models.CharField(
        max_length=20,
        choices=SolicitacaoStatus.choices,
        default=SolicitacaoStatus.PENDENTE,
        db_index=True,
    )
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)
    accepted_at = models.DateTimeField(_('aceito em'), null=True, blank=True)
    a_caminho_at = models.DateTimeField(_('a caminho em'), null=True, blank=True)
    concluded_at = models.DateTimeField(_('concluído em'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelado em'), null=True, blank=True)

    class Meta:
        verbose_name = _('solicitação')
        verbose_name_plural = _('solicitações')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Solicitação #{self.pk} ({self.status})'
