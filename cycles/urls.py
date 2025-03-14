from django.urls import path

from cycles.views import PeriodRecordView, SymptomsRecordView

urlpatterns = [
    path('periods/', PeriodRecordView.as_view(), name='period_record'),
    path('symptoms/', SymptomsRecordView.as_view(), name='symptoms_record'),
]
