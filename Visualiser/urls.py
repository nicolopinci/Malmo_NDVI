from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_season_start', views.get_season_start, name='get_season_start'),
    path('get_errors', views.get_errors, name='get_errors'),
]