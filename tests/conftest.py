import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-pytest-only-not-production-32chars')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.sqlite3')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import Motorista, Prestador, UserRole


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def motorista_user(db):
    User = get_user_model()
    u = User.objects.create_user(
        email='motorista@example.com',
        password='senha12345',
        full_name='Motorista Teste',
        cpf='52998224725',
        role=UserRole.MOTORISTA,
    )
    Motorista.objects.create(user=u)
    return u


@pytest.fixture
def prestador_user(db):
    User = get_user_model()
    u = User.objects.create_user(
        email='prestador@example.com',
        password='senha12345',
        full_name='Prestador Teste',
        cpf='39053344705',
        role=UserRole.PRESTADOR,
    )
    Prestador.objects.create(
        user=u,
        placa='ABC1D23',
        modelo_veiculo='Guincho',
        base_latitude=-19.9,
        base_longitude=-43.9,
        disponivel=True,
    )
    return u


@pytest.fixture
def token_motorista(api, motorista_user):
    r = api.post(
        '/api/v1/auth/token/',
        {'email': 'motorista@example.com', 'password': 'senha12345'},
        format='json',
    )
    assert r.status_code == 200
    return r.json()['access']


@pytest.fixture
def token_prestador(api, prestador_user):
    r = api.post(
        '/api/v1/auth/token/',
        {'email': 'prestador@example.com', 'password': 'senha12345'},
        format='json',
    )
    assert r.status_code == 200
    return r.json()['access']
