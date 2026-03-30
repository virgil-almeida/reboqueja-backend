from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path('users/motoristas/', views.MotoristaCreateView.as_view(), name='motorista-create'),
    path('users/prestadores/disponibilidade/', views.PrestadorDisponibilidadeView.as_view(), name='prestador-disponibilidade'),
    path('users/prestadores/<int:pk>/', views.PrestadorPublicDetailView.as_view(), name='prestador-detail'),
    path('users/prestadores/', views.PrestadorCreateView.as_view(), name='prestador-create'),
    path('users/me/', views.UserMeView.as_view(), name='user-me'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
