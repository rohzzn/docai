from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('search/', views.search, name='search'),
    path('status/', views.api_status, name='api_status'),
    path('health/', views.health, name='health'),
]
