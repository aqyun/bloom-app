from django.urls import path

from . import views

# from .views import news_clustering_view

urlpatterns = [
    path('', views.get_news, name='get_news'),
    path('clusters/', views.cluster_view, name='cluster_view'),
    path('clusters/<int:cluster_id>/all', views.cluster_view_all, name='cluster_view_all'),
    path('clusters/<str:date>/<int:cluster_id>/', views.filtered_cluster_view, name='filtered_cluster_view'),
    path('search/', views.search_results, name='search_results')
]
