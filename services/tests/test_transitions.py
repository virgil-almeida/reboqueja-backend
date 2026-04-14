from django.test import TestCase
from django.utils import timezone

from users.models import Motorista, Prestador, User, UserRole

from services.models import Solicitacao, SolicitacaoStatus
from services.transitions import (
    aplicar_aceite,
    aplicar_cancelamento_motorista,
    aplicar_status_prestador,
)


class TransitionsTests(TestCase):
    def setUp(self):
        self.um = User.objects.create_user(
            email='m@t.com',
            password='x',
            full_name='M',
            cpf='52998224725',
            role=UserRole.MOTORISTA,
        )
        self.m = Motorista.objects.create(user=self.um)
        self.up = User.objects.create_user(
            email='p@t.com',
            password='x',
            full_name='P',
            cpf='39053344705',
            role=UserRole.PRESTADOR,
        )
        self.p = Prestador.objects.create(
            user=self.up,
            placa='ABC1D23',
            modelo_veiculo='X',
            base_latitude=-19.0,
            base_longitude=-43.0,
        )

    def test_cancelar_so_pendente(self):
        s = Solicitacao.objects.create(
            motorista=self.m,
            latitude=-19.9,
            longitude=-43.9,
            descricao='x',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.PENDENTE,
        )
        aplicar_cancelamento_motorista(s)
        s.refresh_from_db()
        self.assertEqual(s.status, SolicitacaoStatus.CANCELADO)
        self.assertIsNotNone(s.cancelled_at)

    def test_cancelar_aceito_falha(self):
        s = Solicitacao.objects.create(
            motorista=self.m,
            prestador=self.p,
            latitude=-19.9,
            longitude=-43.9,
            descricao='x',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.ACEITO,
            accepted_at=timezone.now(),
        )
        with self.assertRaises(ValueError):
            aplicar_cancelamento_motorista(s)

    def test_aceite_em_solicitacao_ja_aceita_levanta_erro(self):
        s = Solicitacao.objects.create(
            motorista=self.m,
            prestador=self.p,
            latitude=-19.9,
            longitude=-43.9,
            descricao='x',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.ACEITO,
            accepted_at=timezone.now(),
        )
        with self.assertRaises(ValueError):
            aplicar_aceite(s, self.p)

    def test_status_por_prestador_nao_vinculado_levanta_erro(self):
        s = Solicitacao.objects.create(
            motorista=self.m,
            prestador=self.p,
            latitude=-19.9,
            longitude=-43.9,
            descricao='x',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.ACEITO,
            accepted_at=timezone.now(),
        )
        outro_user = User.objects.create_user(
            email='p2@t.com', password='x', full_name='P2',
            cpf='86288366757', role=UserRole.PRESTADOR,
        )
        outro_prestador = Prestador.objects.create(
            user=outro_user, placa='DEF4G56', modelo_veiculo='Y',
            base_latitude=-19.0, base_longitude=-43.0,
        )
        with self.assertRaises(ValueError):
            aplicar_status_prestador(s, outro_prestador, SolicitacaoStatus.A_CAMINHO)

    def test_transicao_invalida_levanta_erro(self):
        """ACEITO → CONCLUIDO direto (sem passar por A_CAMINHO) deve falhar."""
        s = Solicitacao.objects.create(
            motorista=self.m,
            prestador=self.p,
            latitude=-19.9,
            longitude=-43.9,
            descricao='x',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.ACEITO,
            accepted_at=timezone.now(),
        )
        with self.assertRaises(ValueError):
            aplicar_status_prestador(s, self.p, SolicitacaoStatus.CONCLUIDO)

    def test_fluxo_prestador(self):
        s = Solicitacao.objects.create(
            motorista=self.m,
            latitude=-19.9,
            longitude=-43.9,
            descricao='x',
            tipo_veiculo='carro',
            status=SolicitacaoStatus.PENDENTE,
        )
        aplicar_aceite(s, self.p)
        s.refresh_from_db()
        self.assertEqual(s.status, SolicitacaoStatus.ACEITO)

        aplicar_status_prestador(s, self.p, SolicitacaoStatus.A_CAMINHO)
        s.refresh_from_db()
        self.assertEqual(s.status, SolicitacaoStatus.A_CAMINHO)
        self.assertIsNotNone(s.a_caminho_at)

        aplicar_status_prestador(s, self.p, SolicitacaoStatus.CONCLUIDO)
        s.refresh_from_db()
        self.assertEqual(s.status, SolicitacaoStatus.CONCLUIDO)
        self.assertIsNotNone(s.concluded_at)
