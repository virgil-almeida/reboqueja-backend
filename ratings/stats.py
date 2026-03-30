from __future__ import annotations

from django.db.models import Avg, Count

from ratings.models import Avaliacao


def prestador_media_e_total(prestador_id: int) -> dict:
    """Média e total de avaliações de um prestador (para serializers e detalhes)."""
    agg = Avaliacao.objects.filter(prestador_id=prestador_id).aggregate(
        media=Avg('nota'),
        total=Count('id'),
    )
    m = agg['media']
    return {
        'media_avaliacoes': round(float(m), 2) if m is not None else None,
        'total_avaliacoes': int(agg['total'] or 0),
    }
