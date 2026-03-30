from django.urls import path

from . import views

urlpatterns = [
    path(
        'services/solicitacoes/meu-historico/',
        views.MotoristaHistoricoListView.as_view(),
        name='motorista-historico',
    ),
    path(
        'services/solicitacoes/meus-atendimentos/',
        views.PrestadorAtendimentosListView.as_view(),
        name='prestador-atendimentos',
    ),
    path(
        'services/solicitacoes/disponiveis/',
        views.SolicitacoesDisponiveisView.as_view(),
        name='solicitacoes-disponiveis',
    ),
    path(
        'services/prestadores/proximos/',
        views.PrestadoresProximosView.as_view(),
        name='prestadores-proximos',
    ),
    path(
        'services/solicitacoes/<int:pk>/cancelar/',
        views.SolicitacaoCancelarView.as_view(),
        name='solicitacao-cancelar',
    ),
    path(
        'services/solicitacoes/<int:pk>/status/',
        views.SolicitacaoPrestadorStatusView.as_view(),
        name='solicitacao-status',
    ),
    path(
        'services/solicitacoes/<int:pk>/aceitar/',
        views.SolicitacaoAceitarView.as_view(),
        name='solicitacao-aceitar',
    ),
    path(
        'services/solicitacoes/<int:pk>/recusar/',
        views.SolicitacaoRecusarView.as_view(),
        name='solicitacao-recusar',
    ),
    path(
        'services/solicitacoes/<int:pk>/',
        views.SolicitacaoDetailView.as_view(),
        name='solicitacao-detail',
    ),
    path(
        'services/solicitacoes/',
        views.SolicitacaoCreateView.as_view(),
        name='solicitacao-create',
    ),
]
