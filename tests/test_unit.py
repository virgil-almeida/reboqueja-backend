"""Testes unitários: models (__str__), UserManager e validators."""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from ratings.models import Avaliacao
from services.models import Solicitacao, SolicitacaoStatus
from users.models import Motorista, Prestador, UserRole
from users.validators import validate_cpf, validate_placa

User = get_user_model()

# ---------------------------------------------------------------------------
# Fixtures locais reutilizáveis
# ---------------------------------------------------------------------------

def _make_motorista(email='m_unit@test.com', cpf='52998224725'):
    u = User.objects.create_user(
        email=email, password='pass', full_name='M Unit',
        cpf=cpf, role=UserRole.MOTORISTA,
    )
    m = Motorista.objects.create(user=u)
    return u, m


def _make_prestador(email='p_unit@test.com', cpf='39053344705', placa='ABC1D23'):
    u = User.objects.create_user(
        email=email, password='pass', full_name='P Unit',
        cpf=cpf, role=UserRole.PRESTADOR,
    )
    p = Prestador.objects.create(
        user=u, placa=placa, modelo_veiculo='Guincho',
        base_latitude=-19.0, base_longitude=-43.0,
    )
    return u, p


# ---------------------------------------------------------------------------
# Models — __str__
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestModelStr:
    def test_user_str(self):
        u, _ = _make_motorista()
        assert str(u) == 'm_unit@test.com'

    def test_motorista_str(self):
        u, m = _make_motorista()
        resultado = str(m)
        assert 'Motorista' in resultado
        assert u.email in resultado

    def test_prestador_str(self):
        u, p = _make_prestador()
        resultado = str(p)
        assert 'Prestador' in resultado
        assert 'ABC1D23' in resultado

    def test_solicitacao_str(self):
        _, m = _make_motorista()
        s = Solicitacao.objects.create(
            motorista=m, latitude=-19.0, longitude=-43.0,
            descricao='Pane', tipo_veiculo='carro',
        )
        assert f'#{s.pk}' in str(s)
        assert 'pendente' in str(s)

    def test_avaliacao_str(self):
        _, m = _make_motorista()
        _, p = _make_prestador()
        s = Solicitacao.objects.create(
            motorista=m, prestador=p,
            latitude=-19.0, longitude=-43.0,
            descricao='Pane', tipo_veiculo='carro',
            status=SolicitacaoStatus.CONCLUIDO,
            concluded_at=timezone.now(),
        )
        a = Avaliacao.objects.create(solicitacao=s, prestador=p, motorista=m, nota=4)
        assert f'#{a.pk}' in str(a)
        assert '4★' in str(a)


# ---------------------------------------------------------------------------
# UserManager
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserManager:
    def test_create_user_email_vazio_levanta_value_error(self):
        with pytest.raises(ValueError, match='e-mail'):
            User.objects.create_user(
                email='', password='pass', full_name='X',
                cpf='52998224725', role=UserRole.MOTORISTA,
            )

    def test_create_superuser_sucesso(self):
        u = User.objects.create_superuser(
            email='admin@test.com', password='adminpass',
            full_name='Admin', cpf='52998224725', role=UserRole.MOTORISTA,
        )
        assert u.is_staff is True
        assert u.is_superuser is True

    def test_create_superuser_is_staff_false_levanta_erro(self):
        with pytest.raises(ValueError, match='is_staff'):
            User.objects.create_superuser(
                email='admin2@test.com', password='adminpass',
                full_name='Admin', cpf='39053344705', role=UserRole.MOTORISTA,
                is_staff=False,
            )

    def test_create_superuser_is_superuser_false_levanta_erro(self):
        with pytest.raises(ValueError, match='is_superuser'):
            User.objects.create_superuser(
                email='admin3@test.com', password='adminpass',
                full_name='Admin', cpf='78187764004', role=UserRole.MOTORISTA,
                is_superuser=False,
            )


# ---------------------------------------------------------------------------
# validate_cpf
# ---------------------------------------------------------------------------

class TestValidateCPF:
    def test_cpf_valido_retorna_somente_digitos(self):
        assert validate_cpf('529.982.247-25') == '52998224725'

    def test_cpf_com_comprimento_invalido_levanta_erro(self):
        with pytest.raises(ValueError, match='inválido'):
            validate_cpf('123')

    def test_cpf_todos_digitos_iguais_levanta_erro(self):
        with pytest.raises(ValueError, match='inválido'):
            validate_cpf('11111111111')

    def test_cpf_primeiro_digito_verificador_errado(self):
        # '52998224725' é válido; trocamos o penúltimo dígito ('2' → '0')
        with pytest.raises(ValueError, match='inválido'):
            validate_cpf('52998224705')

    def test_cpf_segundo_digito_verificador_errado(self):
        # '52998224725' é válido; trocamos o último dígito ('5' → '4')
        with pytest.raises(ValueError, match='inválido'):
            validate_cpf('52998224724')


# ---------------------------------------------------------------------------
# validate_placa
# ---------------------------------------------------------------------------

class TestValidatePlaca:
    def test_placa_mercosul_valida(self):
        assert validate_placa('ABC1D23') == 'ABC1D23'

    def test_placa_mercosul_com_hifen(self):
        assert validate_placa('ABC-1D23') == 'ABC1D23'

    def test_placa_formato_antigo_valido(self):
        assert validate_placa('ABC1234') == 'ABC1234'

    def test_placa_invalida_levanta_erro(self):
        with pytest.raises(ValueError, match='inválida'):
            validate_placa('INVALIDA')

    def test_placa_curta_levanta_erro(self):
        with pytest.raises(ValueError, match='inválida'):
            validate_placa('AB1')
