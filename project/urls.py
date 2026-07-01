from django.urls import path

from . import views

app_name = 'project'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/docs/<int:document_id>/', views.project_document_detail, name='project_document_detail'),
    path('docs/<int:document_id>/upload-images/', views.upload_project_document_images, name='upload_project_document_images'),
    path('import-note/', views.import_project_note, name='import_project_note'),
]
