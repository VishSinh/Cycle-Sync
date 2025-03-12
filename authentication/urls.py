from django.urls import path

from authentication.views import AutenticationView, PingView

urlpatterns = [
    path('auth/', AutenticationView.as_view(), name='authenticate'),
    path('ping/', PingView.as_view(), name='ping'),
]