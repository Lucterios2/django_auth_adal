from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('token/', views.token_exchange, name='token'),
]
