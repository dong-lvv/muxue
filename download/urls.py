from django.urls import path
from . import views

urlpatterns = [
    path('', views.download_center, name='download_center'),
    path('api/category/<str:category_name>/files/', views.category_files, name='category_files'),
    path('download/<str:category_name>/<str:filename>', views.download_file, name='download_file'),
]
