from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Avaliacao(models.Model):
    solicitacao = models.OneToOneField(
        'services.Solicitacao',
        on_delete=models.CASCADE,
        related_name='avaliacao',
        verbose_name=_('solicitação'),
    )
    prestador = models.ForeignKey(
        'users.Prestador',
        on_delete=models.CASCADE,
        related_name='avaliacoes_recebidas',
        verbose_name=_('prestador'),
    )
    motorista = models.ForeignKey(
        'users.Motorista',
        on_delete=models.CASCADE,
        related_name='avaliacoes_feitas',
        verbose_name=_('motorista'),
    )
    nota = models.PositiveSmallIntegerField(
        _('nota'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comentario = models.TextField(_('comentário'), blank=True)
    created_at = models.DateTimeField(_('criado em'), auto_now_add=True)

    class Meta:
        verbose_name = _('avaliação')
        verbose_name_plural = _('avaliações')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Avaliação #{self.pk} — {self.nota}★'
