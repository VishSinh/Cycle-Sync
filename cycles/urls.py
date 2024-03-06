from django.urls import path

from cycles.views import CreatePeriodRecordView, FetchPeriodRecordsView, CreateSymptomsRecordView, FetchSymptomsRecordsView, FetchPeriodRecordDetailsView

urlpatterns = [
    path('periods/add/', CreatePeriodRecordView.as_view(), name='add_period_record'),
    path('periods/fetch/', FetchPeriodRecordsView.as_view(), name='fetch_period_records'),
    path('periods/details/fetch/', FetchPeriodRecordDetailsView.as_view(), name='fetch_period_record_details'),
    path('symptoms/add/', CreateSymptomsRecordView.as_view(), name='add_symptoms_record'),
    path('symptoms/fetch/', FetchSymptomsRecordsView.as_view(), name='fetch_symptoms_records'),
]
