from django.urls import path

from cycles.views import DashboardDetailsView, DashboardView, GetPhaseDetailsView, PeriodRecordView, SymptomsRecordView, CurrentStatusView

urlpatterns = [
    path('periods/', PeriodRecordView.as_view(), name='period_record'),
    path('symptoms/', SymptomsRecordView.as_view(), name='symptoms_record'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/details/', DashboardDetailsView.as_view(), name='dashboard_details'),
    # path('details/', GetPhaseDetailsView.as_view(), name='get_phase_details'),
    path('current-status/', CurrentStatusView.as_view(), name='current_status'),
]
