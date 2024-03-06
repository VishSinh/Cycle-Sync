from django.contrib import admin
from django.urls import path, include

API_VERSION = 'v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path(f'api/{API_VERSION}/', include([
        path('authentication/', include('authentication.urls')),
        path('cycles/', include('cycles.urls')),
        path('users/', include('users.urls')),
    ])),
]