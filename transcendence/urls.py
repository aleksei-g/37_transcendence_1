from django.contrib import admin
from django.urls import path
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/<int:user_id>/', accounts_views.user_page, name='user_page')
]
