import pytest
from django.utils import timezone

from services.models import Solicitacao, SolicitacaoStatus


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
