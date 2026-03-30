from django.contrib import admin

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitacao', 'prestador', 'motorista', 'nota', 'created_at')
    list_filter = ('nota',)
    search_fields = ('solicitacao__id', 'prestador__placa', 'motorista__user__email')
