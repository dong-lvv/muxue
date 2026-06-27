from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog, name='blog'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('api/articles/category/<int:category_id>/', views.get_articles_by_category, name='get_articles_by_category'),
    path('api/article/<int:article_id>/', views.get_article_detail, name='get_article_detail'),
    path('api/search/', views.search_articles, name='search_articles'),
    # Admin 批量上传图片
    path('api/article/<int:article_id>/upload-images/', views.upload_article_images, name='upload_article_images'),
]
