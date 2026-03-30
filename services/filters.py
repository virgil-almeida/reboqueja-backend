import django_filters

from .models import Solicitacao, SolicitacaoStatus


class MotoristaHistoricoFilter(django_filters.FilterSet):
    """Filtros para `GET .../meu-historico/` (US-22)."""

    status = django_filters.ChoiceFilter(choices=SolicitacaoStatus.choices)
    data_inicio = django_filters.DateFilter(method='filter_data_inicio')
    data_fim = django_filters.DateFilter(method='filter_data_fim')

    class Meta:
        model = Solicitacao
        fields = ['status']

    def filter_data_inicio(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(created_at__date__gte=value)

    def filter_data_fim(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(created_at__date__lte=value)
