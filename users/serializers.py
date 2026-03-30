from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Motorista, Prestador, UserRole
from .validators import validate_cpf, validate_placa

User = get_user_model()


class MotoristaCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    cpf = serializers.CharField(max_length=14)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este e-mail já está cadastrado.')
        return value.lower()

    def validate_cpf(self, value):
        try:
            return validate_cpf(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e)) from e

    def validate(self, attrs):
        cpf = attrs.get('cpf')
        if User.objects.filter(cpf=cpf).exists():
            raise serializers.ValidationError({'cpf': 'Este CPF já está cadastrado.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['senha'],
            full_name=validated_data['nome'],
            cpf=validated_data['cpf'],
            role=UserRole.MOTORISTA,
        )
        Motorista.objects.create(user=user)
        return user


class MotoristaResponseSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='full_name')

    class Meta:
        model = User
        fields = ['id', 'nome', 'email', 'cpf']


class PrestadorCreateSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    cpf = serializers.CharField(max_length=14)
    placa = serializers.CharField(max_length=10)
    modelo_veiculo = serializers.CharField(max_length=100)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Este e-mail já está cadastrado.')
        return value.lower()

    def validate_cpf(self, value):
        try:
            return validate_cpf(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e)) from e

    def validate_placa(self, value):
        try:
            return validate_placa(value)
        except ValueError as e:
            raise serializers.ValidationError(str(e)) from e

    def validate(self, attrs):
        cpf = attrs.get('cpf')
        if User.objects.filter(cpf=cpf).exists():
            raise serializers.ValidationError({'cpf': 'Este CPF já está cadastrado.'})
        placa = attrs.get('placa')
        if Prestador.objects.filter(placa=placa).exists():
            raise serializers.ValidationError({'placa': 'Esta placa já está cadastrada.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['senha'],
            full_name=validated_data['nome'],
            cpf=validated_data['cpf'],
            role=UserRole.PRESTADOR,
        )
        Prestador.objects.create(
            user=user,
            placa=validated_data['placa'],
            modelo_veiculo=validated_data['modelo_veiculo'],
            base_latitude=validated_data['latitude'],
            base_longitude=validated_data['longitude'],
            disponivel=True,
        )
        return user


class PrestadorResponseSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='full_name', read_only=True)
    placa = serializers.CharField(source='prestador.placa', read_only=True)
    modelo_veiculo = serializers.CharField(source='prestador.modelo_veiculo', read_only=True)
    latitude = serializers.DecimalField(
        source='prestador.base_latitude',
        max_digits=9,
        decimal_places=6,
        read_only=True,
    )
    longitude = serializers.DecimalField(
        source='prestador.base_longitude',
        max_digits=9,
        decimal_places=6,
        read_only=True,
    )
    disponivel = serializers.BooleanField(source='prestador.disponivel', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'nome',
            'email',
            'cpf',
            'placa',
            'modelo_veiculo',
            'latitude',
            'longitude',
            'disponivel',
        ]

    def to_representation(self, instance):
        if not hasattr(instance, 'prestador'):
            raise serializers.ValidationError('Usuário não é prestador.')
        return super().to_representation(instance)


class PrestadorPublicoSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    telefone = serializers.CharField(source='user.phone', read_only=True)
    latitude = serializers.DecimalField(
        source='base_latitude', max_digits=9, decimal_places=6, read_only=True
    )
    longitude = serializers.DecimalField(
        source='base_longitude', max_digits=9, decimal_places=6, read_only=True
    )

    class Meta:
        model = Prestador
        fields = [
            'id',
            'nome',
            'email',
            'telefone',
            'placa',
            'modelo_veiculo',
            'latitude',
            'longitude',
            'disponivel',
        ]

    def to_representation(self, instance):
        from ratings.stats import prestador_media_e_total

        data = super().to_representation(instance)
        stats = prestador_media_e_total(instance.id)
        data['media_avaliacoes'] = stats['media_avaliacoes']
        data['total_avaliacoes'] = stats['total_avaliacoes']
        return data


class PrestadorDisponibilidadeSerializer(serializers.Serializer):
    disponivel = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance.disponivel = validated_data['disponivel']
        instance.save(update_fields=['disponivel'])
        return instance


class UserMeSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source='full_name', required=False)
    telefone = serializers.CharField(source='phone', required=False, allow_blank=True)
    foto = serializers.URLField(source='photo_url', required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'nome', 'email', 'cpf', 'telefone', 'foto', 'role']
        read_only_fields = ['id', 'email', 'cpf', 'role']
