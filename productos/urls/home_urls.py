from django.urls import path
from productos.views.home_view import home

urlpatterns = [
    path('', home, name='home'),
]
