"""
Máquina de estados da solicitação (US-14).
Fluxo principal: pendente → aceito → a_caminho → concluído.
Cancelamento (motorista, US-13): apenas a partir de pendente.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils import timezone

from .models import Solicitacao, SolicitacaoStatus

if TYPE_CHECKING:
    from users.models import Prestador


def aplicar_aceite(solicitacao: Solicitacao, prestador: Prestador) -> None:
    if solicitacao.status != SolicitacaoStatus.PENDENTE or solicitacao.prestador_id is not None:
        raise ValueError('A solicitação não está disponível para aceite.')
    now = timezone.now()
    solicitacao.prestador = prestador
    solicitacao.status = SolicitacaoStatus.ACEITO
    solicitacao.accepted_at = now
    solicitacao.save(update_fields=['prestador', 'status', 'accepted_at'])


def aplicar_cancelamento_motorista(solicitacao: Solicitacao) -> None:
    """Cancelamento pelo motorista: somente se pendente (US-13)."""
    if solicitacao.status != SolicitacaoStatus.PENDENTE:
        raise ValueError(
            'Não é possível cancelar: a solicitação já foi aceita ou não está mais pendente.',
        )
    now = timezone.now()
    solicitacao.status = SolicitacaoStatus.CANCELADO
    solicitacao.cancelled_at = now
    solicitacao.save(update_fields=['status', 'cancelled_at'])


def aplicar_status_prestador(
    solicitacao: Solicitacao,
    prestador: Prestador,
    novo_status: str,
) -> None:
    """Transições: aceito → a_caminho; a_caminho → concluído (US-15)."""
    if solicitacao.prestador_id != prestador.id:
        raise ValueError('Apenas o prestador vinculado pode atualizar o status desta solicitação.')

    atual = solicitacao.status
    if atual == SolicitacaoStatus.ACEITO and novo_status == SolicitacaoStatus.A_CAMINHO:
        now = timezone.now()
        solicitacao.status = SolicitacaoStatus.A_CAMINHO
        solicitacao.a_caminho_at = now
        solicitacao.save(update_fields=['status', 'a_caminho_at'])
        return

    if atual == SolicitacaoStatus.A_CAMINHO and novo_status == SolicitacaoStatus.CONCLUIDO:
        now = timezone.now()
        solicitacao.status = SolicitacaoStatus.CONCLUIDO
        solicitacao.concluded_at = now
        solicitacao.save(update_fields=['status', 'concluded_at'])
        return

    raise ValueError(
        f'Transição inválida de "{atual}" para "{novo_status}". '
        'Permitido: aceito → a_caminho; a_caminho → concluído.',
    )
