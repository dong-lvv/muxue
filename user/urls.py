from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('api/login/', views.login, name='api_login'),
    path('api/register/', views.register, name='api_register'),
    path('api/logout/', views.logout, name='api_logout'),
    path('api/user-info/', views.get_user_info, name='api_user_info'),
    path('api/send-verification-code/', views.send_verification_code, name='api_send_verification_code'),
]
