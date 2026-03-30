from django import forms
from django.contrib import admin

from .models import Motorista, Prestador, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'cpf', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Perfil', {'fields': ('full_name', 'cpf', 'phone', 'photo_url', 'role')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas', {'fields': ('last_login', 'date_joined')}),
    )


class MotoristaAdminForm(forms.ModelForm):
    is_active = forms.BooleanField(label='Conta ativa', required=False)

    class Meta:
        model = Motorista
        fields = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['is_active'].initial = self.instance.user.is_active

    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            obj.save()
            if 'is_active' in self.cleaned_data:
                obj.user.is_active = self.cleaned_data['is_active']
                obj.user.save()
        return obj


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    form = MotoristaAdminForm
    list_display = ('id', 'email', 'nome', 'cpf', 'conta_ativa')
    list_filter = ('user__is_active',)
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('user',)
    fields = ('user', 'is_active')

    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.user.email

    @admin.display(description='Nome')
    def nome(self, obj):
        return obj.user.full_name

    @admin.display(description='CPF')
    def cpf(self, obj):
        return obj.user.cpf

    @admin.display(description='Conta ativa', boolean=True)
    def conta_ativa(self, obj):
        return obj.user.is_active


class PrestadorAdminForm(forms.ModelForm):
    is_active = forms.BooleanField(label='Conta ativa', required=False)

    class Meta:
        model = Prestador
        fields = ['user', 'placa', 'modelo_veiculo', 'base_latitude', 'base_longitude', 'disponivel']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['is_active'].initial = self.instance.user.is_active

    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            obj.save()
            if 'is_active' in self.cleaned_data:
                obj.user.is_active = self.cleaned_data['is_active']
                obj.user.save()
        return obj


@admin.register(Prestador)
class PrestadorAdmin(admin.ModelAdmin):
    form = PrestadorAdminForm
    list_display = ('id', 'email', 'nome', 'placa', 'modelo_veiculo', 'disponivel', 'conta_ativa')
    list_filter = ('user__is_active', 'disponivel')
    search_fields = ('user__email', 'user__full_name', 'placa')
    readonly_fields = ('user',)
    fields = (
        'user',
        'placa',
        'modelo_veiculo',
        'base_latitude',
        'base_longitude',
        'disponivel',
        'is_active',
    )

    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.user.email

    @admin.display(description='Nome')
    def nome(self, obj):
        return obj.user.full_name

    @admin.display(description='Conta ativa', boolean=True)
    def conta_ativa(self, obj):
        return obj.user.is_active
