from django.urls import path

from users.views import AddUserDetailsView, FetchUserDetails

urlpatterns = [
    path('details/add/', AddUserDetailsView.as_view(), name='add_user_details'),
    path('details/fetch/', FetchUserDetails.as_view(), name='fetch_user_details'),
]