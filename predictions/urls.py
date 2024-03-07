from django.urls import path

from predictions.views import CreateCycleStatPredictionView, CreatePredictionView


urlpatterns = [
    path('create/', CreatePredictionView.as_view(), name='create_prediction'),
    path('cycle/stat/create/', CreateCycleStatPredictionView.as_view(), name='create_cycle_stat_prediction'),
]
