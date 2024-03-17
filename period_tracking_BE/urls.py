from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path(f'api/v1/', include([
        path('auth/', include('authentication.urls')),
        path('cycles/', include('cycles.urls')),
        path('users/', include('users.urls')),
        path('predictions/', include('predictions.urls')),
    ])),
]