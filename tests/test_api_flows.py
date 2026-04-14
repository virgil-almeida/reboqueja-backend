import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from services.models import Solicitacao, SolicitacaoStatus
from users.models import Motorista, Prestador, UserRole


@pytest.mark.django_db
class TestCadastroLogin:
    def test_cadastro_motorista_e_login(self, api):
        r = api.post(
            '/api/v1/users/motoristas/',
            {
                'nome': 'João',
                'email': 'joao@test.com',
                'senha': 'senha12345',
                'cpf': '11144477735',
            },
            format='json',
        )
        assert r.status_code == 201
        assert 'senha' not in r.json()
        r2 = api.post(
            '/api/v1/auth/token/',
            {'email': 'joao@test.com', 'password': 'senha12345'},
            format='json',
        )
        assert r2.status_code == 200
        assert 'access' in r2.json()


@pytest.mark.django_db
class TestFluxoSolicitacaoCompleto:
    def test_criar_aceitar_concluir_avaliar(
        self,
        api,
        motorista_user,
        prestador_user,
        token_motorista,
        token_prestador,
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.post(
            '/api/v1/services/solicitacoes/',
            {
                'latitude': '-19.92',
                'longitude': '-43.92',
                'descricao': 'Pane',
                'tipo_veiculo': 'carro',
            },
            format='json',
            **h_m,
        )
        assert r.status_code == 201
        sid = r.json()['id']
        assert r.json()['status'] == 'pendente'

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', {}, format='json', **h_p)
        assert r.status_code == 200
        assert r.json()['status'] == 'aceito'

        det = api.get(f'/api/v1/services/solicitacoes/{sid}/', **h_m)
        assert det.status_code == 200
        p = det.json()['prestador']
        assert p is not None
        assert 'media_avaliacoes' in p
        assert p['placa'] == 'ABC1D23'

        r = api.post(
            f'/api/v1/services/solicitacoes/{sid}/status/',
            {'status': 'a_caminho'},
            format='json',
            **h_p,
        )
        assert r.status_code == 200
        r = api.post(
            f'/api/v1/services/solicitacoes/{sid}/status/',
            {'status': 'concluido'},
            format='json',
            **h_p,
        )
        assert r.status_code == 200
        assert r.json()['status'] == 'concluido'

        r = api.post(
            '/api/v1/ratings/',
            {'solicitacao_id': sid, 'nota': 5, 'comentario': 'Ótimo'},
            format='json',
            **h_m,
        )
        assert r.status_code == 201
        assert r.json()['nota'] == 5


@pytest.mark.django_db
class TestHistoricoFiltros:
    def test_filtro_status_e_data(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        m = motorista_user.motorista
        Solicitacao.objects.create(
            motorista=m,
            latitude=-19.0,
            longitude=-43.0,
            descricao='a',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.CONCLUIDO,
            concluded_at=timezone.now(),
        )
        Solicitacao.objects.create(
            motorista=m,
            latitude=-19.0,
            longitude=-43.0,
            descricao='b',
            tipo_veiculo='moto',
            status=SolicitacaoStatus.CANCELADO,
            cancelled_at=timezone.now(),
        )
        r = api.get(
            '/api/v1/services/solicitacoes/meu-historico/?status=concluido',
            **h,
        )
        assert r.status_code == 200
        body = r.json()
        assert 'results' in body
        assert all(x['status'] == 'concluido' for x in body['results'])


@pytest.mark.django_db
class TestOpenApi:
    def test_schema_e_swagger(self, api):
        r = api.get('/api/schema/')
        assert r.status_code == 200
        assert b'openapi' in r.content
        r2 = api.get('/api/docs/')
        assert r2.status_code == 200


# ---------------------------------------------------------------------------
# Helpers compartilhados
# ---------------------------------------------------------------------------

def _criar_solicitacao(api, token):
    h = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    r = api.post(
        '/api/v1/services/solicitacoes/',
        {'latitude': '-19.92', 'longitude': '-43.92', 'descricao': 'Pane seca', 'tipo_veiculo': 'carro'},
        format='json',
        **h,
    )
    assert r.status_code == 201
    return r.json()['id']


def _segundo_motorista(api):
    """Cria um motorista adicional e retorna (user, token)."""
    User = get_user_model()
    u = User.objects.create_user(
        email='motorista2@test.com',
        password='senha12345',
        full_name='Motorista Dois',
        cpf='78187764004',
        role=UserRole.MOTORISTA,
    )
    Motorista.objects.create(user=u)
    r = api.post('/api/v1/auth/token/', {'email': 'motorista2@test.com', 'password': 'senha12345'}, format='json')
    return u, r.json()['access']


# ---------------------------------------------------------------------------
# US-13 — Cancelar solicitação (endpoint HTTP)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCancelarSolicitacao:
    def test_cancelar_pendente(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        sid = _criar_solicitacao(api, token_motorista)

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/cancelar/', format='json', **h)

        assert r.status_code == 200
        body = r.json()
        assert body['status'] == 'cancelado'
        assert body['timestamps']['cancelado_em'] is not None

    def test_cancelar_aceita_retorna_400(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/cancelar/', format='json', **h_m)

        assert r.status_code == 400
        assert 'detail' in r.json()

    def test_cancelar_solicitacao_de_outro_motorista_retorna_404(
        self, api, motorista_user, token_motorista
    ):
        sid = _criar_solicitacao(api, token_motorista)
        _, outro_token = _segundo_motorista(api)
        h_outro = {'HTTP_AUTHORIZATION': f'Bearer {outro_token}'}

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/cancelar/', format='json', **h_outro)

        assert r.status_code == 404

    def test_sem_autenticacao_retorna_401(self, api, motorista_user, token_motorista):
        sid = _criar_solicitacao(api, token_motorista)

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/cancelar/', format='json')

        assert r.status_code == 401


# ---------------------------------------------------------------------------
# US-10 — Listar solicitações disponíveis (prestador)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSolicitacoesDisponiveis:
    def test_lista_solicitacoes_no_raio(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        _criar_solicitacao(api, token_motorista)

        # Prestador consulta a partir da sua base (-19.9, -43.9); solicitação criada a ~3 km
        r = api.get('/api/v1/services/solicitacoes/disponiveis/?lat=-19.9&lng=-43.9', **h_p)

        assert r.status_code == 200
        assert len(r.json()) >= 1
        item = r.json()[0]
        assert 'distancia_km' in item
        assert item['distancia_km'] < 30

    def test_prestador_indisponivel_retorna_lista_vazia(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        _criar_solicitacao(api, token_motorista)
        api.patch('/api/v1/users/prestadores/disponibilidade/', {'disponivel': False}, format='json', **h_p)

        r = api.get('/api/v1/services/solicitacoes/disponiveis/?lat=-19.9&lng=-43.9', **h_p)

        assert r.status_code == 200
        assert r.json() == []

    def test_sem_lat_lng_retorna_400(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.get('/api/v1/services/solicitacoes/disponiveis/', **h_p)

        assert r.status_code == 400

    def test_raio_zero_retorna_400(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.get('/api/v1/services/solicitacoes/disponiveis/?lat=-19.9&lng=-43.9&raio=0', **h_p)

        assert r.status_code == 400

    def test_solicitacao_aceita_nao_aparece(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        r = api.get('/api/v1/services/solicitacoes/disponiveis/?lat=-19.9&lng=-43.9', **h_p)

        assert r.status_code == 200
        assert sid not in [s['id'] for s in r.json()]


# ---------------------------------------------------------------------------
# Prestadores próximos
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPrestadoresProximos:
    def test_lista_prestadores_no_raio(self, api, prestador_user, token_motorista):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        # Prestador base está em -19.9, -43.9; consulta do mesmo ponto → distância 0
        r = api.get('/api/v1/services/prestadores/proximos/?lat=-19.9&lng=-43.9', **h_m)

        assert r.status_code == 200
        assert len(r.json()) >= 1
        item = r.json()[0]
        assert item['distancia_km'] == 0.0
        assert 'placa' in item

    def test_prestador_indisponivel_nao_aparece(
        self, api, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        api.patch('/api/v1/users/prestadores/disponibilidade/', {'disponivel': False}, format='json', **h_p)

        r = api.get('/api/v1/services/prestadores/proximos/?lat=-19.9&lng=-43.9', **h_m)

        assert r.status_code == 200
        assert r.json() == []

    def test_sem_lat_lng_retorna_400(self, api, motorista_user, token_motorista):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.get('/api/v1/services/prestadores/proximos/', **h_m)

        assert r.status_code == 400

    def test_raio_invalido_retorna_400(self, api, motorista_user, token_motorista):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.get('/api/v1/services/prestadores/proximos/?lat=-19.9&lng=-43.9&raio=-5', **h_m)

        assert r.status_code == 400


# ---------------------------------------------------------------------------
# US-11 — Recusar solicitação
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRecusarSolicitacao:
    def test_recusar_retorna_204_e_solicitacao_permanece_pendente(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/recusar/', format='json', **h_p)

        assert r.status_code == 204
        # Solicitação deve continuar pendente
        detalhe = api.get(f'/api/v1/services/solicitacoes/{sid}/', **h_m)
        assert detalhe.json()['status'] == 'pendente'

    def test_recusar_inexistente_retorna_404(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.post('/api/v1/services/solicitacoes/99999/recusar/', format='json', **h_p)

        assert r.status_code == 404


# ---------------------------------------------------------------------------
# US-07 — Disponibilidade do prestador
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDisponibilidadePrestador:
    def test_desativar_disponibilidade(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.patch(
            '/api/v1/users/prestadores/disponibilidade/', {'disponivel': False}, format='json', **h_p
        )

        assert r.status_code == 200
        assert r.json()['disponivel'] is False

    def test_ativar_disponibilidade(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        api.patch('/api/v1/users/prestadores/disponibilidade/', {'disponivel': False}, format='json', **h_p)

        r = api.patch(
            '/api/v1/users/prestadores/disponibilidade/', {'disponivel': True}, format='json', **h_p
        )

        assert r.status_code == 200
        assert r.json()['disponivel'] is True

    def test_motorista_nao_pode_alterar_retorna_403(self, api, motorista_user, token_motorista):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.patch(
            '/api/v1/users/prestadores/disponibilidade/', {'disponivel': False}, format='json', **h_m
        )

        assert r.status_code == 403


# ---------------------------------------------------------------------------
# US-05 — Atualizar perfil (/me/)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAtualizarPerfil:
    def test_atualizar_nome_e_telefone(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.patch(
            '/api/v1/users/me/', {'nome': 'Nome Atualizado', 'telefone': '31999990000'}, format='json', **h
        )

        assert r.status_code == 200
        assert r.json()['nome'] == 'Nome Atualizado'
        assert r.json()['telefone'] == '31999990000'

    def test_email_e_cpf_sao_readonly(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        email_original = motorista_user.email
        cpf_original = motorista_user.cpf

        r = api.patch(
            '/api/v1/users/me/', {'email': 'outro@email.com', 'cpf': '00000000000'}, format='json', **h
        )

        assert r.status_code == 200
        assert r.json()['email'] == email_original
        assert r.json()['cpf'] == cpf_original

    def test_sem_autenticacao_retorna_401(self, api):
        r = api.patch('/api/v1/users/me/', {'nome': 'Qualquer'}, format='json')

        assert r.status_code == 401

    def test_get_perfil_proprio(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.get('/api/v1/users/me/', **h)

        assert r.status_code == 200
        assert r.json()['email'] == motorista_user.email
        assert 'senha' not in r.json()


# ---------------------------------------------------------------------------
# US-21 — Histórico de atendimentos do prestador
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHistoricoPrestador:
    def test_lista_atendimentos_paginado(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'a_caminho'}, format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'concluido'}, format='json', **h_p)

        r = api.get('/api/v1/services/solicitacoes/meus-atendimentos/', **h_p)

        assert r.status_code == 200
        body = r.json()
        assert 'results' in body
        assert len(body['results']) == 1
        item = body['results'][0]
        assert item['id'] == sid
        assert item['status'] == 'concluido'
        assert item['motorista']['email'] == motorista_user.email
        assert item['avaliacao_recebida'] is None  # ainda não avaliado

    def test_avaliacao_recebida_aparece_no_historico(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'a_caminho'}, format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'concluido'}, format='json', **h_p)
        api.post('/api/v1/ratings/', {'solicitacao_id': sid, 'nota': 4, 'comentario': 'Bom'}, format='json', **h_m)

        r = api.get('/api/v1/services/solicitacoes/meus-atendimentos/', **h_p)

        item = r.json()['results'][0]
        assert item['avaliacao_recebida']['nota'] == 4
        assert item['avaliacao_recebida']['comentario'] == 'Bom'

    def test_sem_atendimentos_retorna_lista_vazia(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.get('/api/v1/services/solicitacoes/meus-atendimentos/', **h_p)

        assert r.status_code == 200
        assert r.json()['results'] == []

    def test_motorista_nao_pode_acessar_retorna_403(self, api, motorista_user, token_motorista):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.get('/api/v1/services/solicitacoes/meus-atendimentos/', **h_m)

        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Helpers adicionais
# ---------------------------------------------------------------------------

def _segundo_prestador(api):
    """Cria um segundo prestador e devolve (user, token)."""
    User = get_user_model()
    u = User.objects.create_user(
        email='prestador2@test.com',
        password='senha12345',
        full_name='Prestador Dois',
        cpf='86288366757',
        role=UserRole.PRESTADOR,
    )
    Prestador.objects.create(
        user=u,
        placa='DEF4G56',
        modelo_veiculo='Guincho2',
        base_latitude=-19.9,
        base_longitude=-43.9,
        disponivel=True,
    )
    r = api.post(
        '/api/v1/auth/token/',
        {'email': 'prestador2@test.com', 'password': 'senha12345'},
        format='json',
    )
    return u, r.json()['access']


# ---------------------------------------------------------------------------
# US-03 — Cadastro de prestador via API
# ---------------------------------------------------------------------------

_PAYLOAD_PRESTADOR = {
    'nome': 'Maria',
    'email': 'maria@test.com',
    'senha': 'senha12345',
    'cpf': '86288366757',
    'placa': 'XYZ9W87',
    'modelo_veiculo': 'Guincho',
    'latitude': '-19.9',
    'longitude': '-43.9',
}


@pytest.mark.django_db
class TestCadastroPrestador:
    def test_cadastro_sucesso(self, api):
        r = api.post('/api/v1/users/prestadores/', _PAYLOAD_PRESTADOR, format='json')
        assert r.status_code == 201
        body = r.json()
        assert body['placa'] == 'XYZ9W87'
        assert 'senha' not in body

    def test_email_duplicado_retorna_400(self, api, prestador_user):
        payload = {**_PAYLOAD_PRESTADOR, 'email': prestador_user.email}
        r = api.post('/api/v1/users/prestadores/', payload, format='json')
        assert r.status_code == 400

    def test_cpf_invalido_retorna_400(self, api):
        r = api.post(
            '/api/v1/users/prestadores/',
            {**_PAYLOAD_PRESTADOR, 'cpf': '00000000000'},
            format='json',
        )
        assert r.status_code == 400

    def test_placa_invalida_retorna_400(self, api):
        r = api.post(
            '/api/v1/users/prestadores/',
            {**_PAYLOAD_PRESTADOR, 'placa': 'INVALIDA'},
            format='json',
        )
        assert r.status_code == 400

    def test_cpf_duplicado_retorna_400(self, api, prestador_user):
        payload = {**_PAYLOAD_PRESTADOR, 'cpf': prestador_user.cpf}
        r = api.post('/api/v1/users/prestadores/', payload, format='json')
        assert r.status_code == 400

    def test_placa_duplicada_retorna_400(self, api, prestador_user):
        payload = {**_PAYLOAD_PRESTADOR, 'placa': prestador_user.prestador.placa}
        r = api.post('/api/v1/users/prestadores/', payload, format='json')
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# US-02 — Validações de cadastro de motorista
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCadastroMotoristaValidacoes:
    def test_email_duplicado_retorna_400(self, api, motorista_user):
        r = api.post(
            '/api/v1/users/motoristas/',
            {
                'nome': 'Outro',
                'email': motorista_user.email,
                'senha': 'senha12345',
                'cpf': '86288366757',
            },
            format='json',
        )
        assert r.status_code == 400

    def test_cpf_invalido_retorna_400(self, api):
        r = api.post(
            '/api/v1/users/motoristas/',
            {
                'nome': 'Teste',
                'email': 'cpfinvalido@test.com',
                'senha': 'senha12345',
                'cpf': '00000000000',
            },
            format='json',
        )
        assert r.status_code == 400

    def test_cpf_duplicado_retorna_400(self, api, motorista_user):
        r = api.post(
            '/api/v1/users/motoristas/',
            {
                'nome': 'Outro',
                'email': 'outro@test.com',
                'senha': 'senha12345',
                'cpf': motorista_user.cpf,
            },
            format='json',
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# US-19 — Perfil público do prestador
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestPrestadorPerfilPublico:
    def test_get_perfil_retorna_media_e_total(self, api, prestador_user):
        pk = prestador_user.prestador.id
        r = api.get(f'/api/v1/users/prestadores/{pk}/')
        assert r.status_code == 200
        body = r.json()
        assert 'media_avaliacoes' in body
        assert 'total_avaliacoes' in body
        assert body['total_avaliacoes'] == 0
        assert body['media_avaliacoes'] is None


# ---------------------------------------------------------------------------
# US-08 — Bloquear segunda solicitação ativa
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSolicitacaoAtiva:
    def test_segunda_solicitacao_ativa_retorna_400(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        _criar_solicitacao(api, token_motorista)

        r = api.post(
            '/api/v1/services/solicitacoes/',
            {'latitude': '-19.92', 'longitude': '-43.92', 'descricao': 'Outra', 'tipo_veiculo': 'moto'},
            format='json',
            **h,
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# US-20 — Histórico do motorista com prestador e avaliação
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHistoricoMotoristaCompleto:
    def test_historico_exibe_prestador_e_avaliacao(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        # Fluxo completo com avaliação
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'a_caminho'}, format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'concluido'}, format='json', **h_p)
        api.post('/api/v1/ratings/', {'solicitacao_id': sid, 'nota': 5, 'comentario': 'Ótimo'}, format='json', **h_m)

        r = api.get('/api/v1/services/solicitacoes/meu-historico/', **h_m)

        assert r.status_code == 200
        item = r.json()['results'][0]
        assert item['prestador'] is not None
        assert item['prestador']['placa'] == prestador_user.prestador.placa
        assert item['avaliacao']['nota'] == 5


# ---------------------------------------------------------------------------
# US-18 — Validações de avaliação
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAvaliacaoValidacoes:
    def test_avaliar_solicitacao_de_outro_motorista_retorna_400(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        # Completa o fluxo com motorista1
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'a_caminho'}, format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'concluido'}, format='json', **h_p)

        # Motorista2 tenta avaliar a solicitação de motorista1
        User = get_user_model()
        outro_user = User.objects.create_user(
            email='m2_aval@test.com', password='senha12345', full_name='M2',
            cpf='78187764004', role=UserRole.MOTORISTA,
        )
        Motorista.objects.create(user=outro_user)
        r2 = api.post('/api/v1/auth/token/', {'email': 'm2_aval@test.com', 'password': 'senha12345'}, format='json')
        h_m2 = {'HTTP_AUTHORIZATION': f'Bearer {r2.json()["access"]}'}

        r = api.post('/api/v1/ratings/', {'solicitacao_id': sid, 'nota': 3}, format='json', **h_m2)
        assert r.status_code == 400

    def test_avaliar_antes_de_concluir_retorna_400(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        # Status ainda é 'aceito', não 'concluido'
        r = api.post('/api/v1/ratings/', {'solicitacao_id': sid, 'nota': 5}, format='json', **h_m)
        assert r.status_code == 400

    def test_avaliar_duas_vezes_retorna_400(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'a_caminho'}, format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'concluido'}, format='json', **h_p)
        api.post('/api/v1/ratings/', {'solicitacao_id': sid, 'nota': 5}, format='json', **h_m)

        r = api.post('/api/v1/ratings/', {'solicitacao_id': sid, 'nota': 4}, format='json', **h_m)
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# US-22 — Filtros de data no histórico do motorista
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestHistoricoFiltrosData:
    def _seed(self, motorista):
        return Solicitacao.objects.create(
            motorista=motorista,
            latitude=-19.0, longitude=-43.0,
            descricao='x', tipo_veiculo='carro',
            status=SolicitacaoStatus.CONCLUIDO,
            concluded_at=timezone.now(),
        )

    def test_filtro_data_inicio_retorna_resultados(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        self._seed(motorista_user.motorista)

        r = api.get('/api/v1/services/solicitacoes/meu-historico/?data_inicio=2000-01-01', **h)

        assert r.status_code == 200
        assert len(r.json()['results']) >= 1

    def test_filtro_data_inicio_futuro_retorna_vazio(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        self._seed(motorista_user.motorista)

        r = api.get('/api/v1/services/solicitacoes/meu-historico/?data_inicio=2099-12-31', **h)

        assert r.status_code == 200
        assert r.json()['results'] == []

    def test_filtro_data_fim_retorna_resultados(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        self._seed(motorista_user.motorista)

        r = api.get('/api/v1/services/solicitacoes/meu-historico/?data_fim=2099-12-31', **h)

        assert r.status_code == 200
        assert len(r.json()['results']) >= 1

    def test_filtro_data_fim_passado_retorna_vazio(self, api, motorista_user, token_motorista):
        h = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        self._seed(motorista_user.motorista)

        r = api.get('/api/v1/services/solicitacoes/meu-historico/?data_fim=2000-01-01', **h)

        assert r.status_code == 200
        assert r.json()['results'] == []


# ---------------------------------------------------------------------------
# US-15 — Edge cases do endpoint de status
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStatusUpdateEdgeCases:
    def test_solicitacao_inexistente_retorna_404(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.post(
            '/api/v1/services/solicitacoes/99999/status/',
            {'status': 'a_caminho'},
            format='json',
            **h_p,
        )
        assert r.status_code == 404

    def test_prestador_nao_vinculado_retorna_400(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        # Prestador1 aceita
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        # Prestador2 tenta atualizar status
        _, token_p2 = _segundo_prestador(api)
        h_p2 = {'HTTP_AUTHORIZATION': f'Bearer {token_p2}'}
        r = api.post(
            f'/api/v1/services/solicitacoes/{sid}/status/',
            {'status': 'a_caminho'},
            format='json',
            **h_p2,
        )
        assert r.status_code == 400

    def test_transicao_invalida_retorna_400(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        # Aceita e vai para a_caminho e concluido
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'a_caminho'}, format='json', **h_p)
        api.post(f'/api/v1/services/solicitacoes/{sid}/status/', {'status': 'concluido'}, format='json', **h_p)

        # Tenta atualizar de novo a partir de concluido (transição inválida)
        r = api.post(
            f'/api/v1/services/solicitacoes/{sid}/status/',
            {'status': 'a_caminho'},
            format='json',
            **h_p,
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Raio com string inválida (silenciosamente usa 30 km)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRaioStringInvalida:
    def test_prestadores_proximos_raio_string_usa_padrao(self, api, prestador_user, token_motorista):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}

        r = api.get('/api/v1/services/prestadores/proximos/?lat=-19.9&lng=-43.9&raio=abc', **h_m)

        # Deve usar raio padrão (30 km) e retornar normalmente
        assert r.status_code == 200

    def test_solicitacoes_disponiveis_raio_string_usa_padrao(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        _criar_solicitacao(api, token_motorista)

        r = api.get(
            '/api/v1/services/solicitacoes/disponiveis/?lat=-19.9&lng=-43.9&raio=abc',
            **h_p,
        )

        assert r.status_code == 200


# ---------------------------------------------------------------------------
# US-11 — Edge cases de aceitar
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAceitarEdgeCases:
    def test_prestador_indisponivel_retorna_403(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_m = {'HTTP_AUTHORIZATION': f'Bearer {token_motorista}'}
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.patch('/api/v1/users/prestadores/disponibilidade/', {'disponivel': False}, format='json', **h_p)

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        assert r.status_code == 403

    def test_solicitacao_inexistente_retorna_404(self, api, prestador_user, token_prestador):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}

        r = api.post('/api/v1/services/solicitacoes/99999/aceitar/', format='json', **h_p)

        assert r.status_code == 404

    def test_mesmo_prestador_aceita_duas_vezes_e_idempotente(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        assert r.status_code == 200
        assert r.json()['status'] == 'aceito'

    def test_outro_prestador_aceita_solicitacao_ja_aceita_retorna_409(
        self, api, motorista_user, prestador_user, token_motorista, token_prestador
    ):
        h_p = {'HTTP_AUTHORIZATION': f'Bearer {token_prestador}'}
        sid = _criar_solicitacao(api, token_motorista)
        api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p)

        _, token_p2 = _segundo_prestador(api)
        h_p2 = {'HTTP_AUTHORIZATION': f'Bearer {token_p2}'}

        r = api.post(f'/api/v1/services/solicitacoes/{sid}/aceitar/', format='json', **h_p2)

        assert r.status_code == 409
