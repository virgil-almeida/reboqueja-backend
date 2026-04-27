from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    MOTORISTA = 'motorista', _('Motorista')
    PRESTADOR = 'prestador', _('Prestador')


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_('e-mail'), unique=True)
    cpf = models.CharField(_('CPF'), max_length=11, unique=True, db_index=True)
    full_name = models.CharField(_('nome completo'), max_length=255)
    phone = models.CharField(_('telefone'), max_length=20, blank=True)
    photo_url = models.URLField(_('URL da foto'), blank=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'cpf', 'role']

    objects = UserManager()

    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')

    def __str__(self) -> str:
        return self.email


class Motorista(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='motorista',
        verbose_name=_('usuário'),
    )

    class Meta:
        verbose_name = _('motorista')
        verbose_name_plural = _('motoristas')

    def __str__(self) -> str:
        return f'Motorista {self.user.email}'


class Prestador(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='prestador',
        verbose_name=_('usuário'),
    )
    placa = models.CharField(_('placa'), max_length=8, unique=True)
    modelo_veiculo = models.CharField(_('modelo do veículo'), max_length=100)
    base_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    base_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    disponivel = models.BooleanField(
        _('disponível para matching'),
        default=True,
        help_text=_('Quando falso, o prestador não entra no matching de solicitações.'),
    )

    class Meta:
        verbose_name = _('prestador')
        verbose_name_plural = _('prestadores')

    def __str__(self) -> str:
        return f'Prestador {self.user.email} ({self.placa})'
