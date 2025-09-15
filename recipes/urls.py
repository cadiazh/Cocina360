from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('recipe/<int:pk>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('recipe/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('<int:recipe_pk>/ingredient/<int:ingredient_pk>/toggle/', views.toggle_ingredient_completion, name='toggle_ingredient_completion'),
    path('<int:recipe_pk>/step/<int:step_pk>/toggle/', views.toggle_step_completion, name='toggle_step_completion'),
    path('recipes/<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('accounts/', include('django.contrib.auth.urls')),  
    path('accounts/register/', views.register, name='register'),
    path('recipes/new/', views.recipe_create, name='recipe_create'),

]
