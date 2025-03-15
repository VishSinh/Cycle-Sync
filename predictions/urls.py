from django.urls import path

from predictions.views import PredictionView


urlpatterns = [
    path('', PredictionView.as_view(), name='create_prediction'),
]
