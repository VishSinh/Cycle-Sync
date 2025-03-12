from django.urls import path

from users.views import UserDetailsView

urlpatterns = [
    path('details/', UserDetailsView.as_view(), name='user_details'),
]