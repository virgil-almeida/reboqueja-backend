from django.urls import path

from . import views

urlpatterns = [
    path('ratings/', views.AvaliacaoCreateView.as_view(), name='rating-create'),
]
