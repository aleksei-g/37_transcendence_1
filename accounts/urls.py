from django.urls import path
from accounts import views


urlpatterns = [
    path('<int:user_id>/', views.user_page, name='user_page'),
]
