"""Factories (factory_boy) para testes — US-24."""
import factory

from users.models import User, UserRole


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@factory.test')
    full_name = factory.Faker('name', locale='pt_BR')
    cpf = factory.Iterator(['52998224725', '39053344705', '11144477735', '86288366757'])
    role = UserRole.MOTORISTA

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'senha12345')
        return model_class.objects.create_user(password=password, *args, **kwargs)
