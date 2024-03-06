from django.urls import path

from authentication.views import AutenticationView

urlpatterns = [
    path('', AutenticationView.as_view(), name='authenticate'),
]