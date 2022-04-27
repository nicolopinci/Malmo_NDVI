from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('Visualiser/', include('Visualiser.urls')),
    path('admin/', admin.site.urls),
]