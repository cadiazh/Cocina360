from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('<int:recipe_pk>/ingredient/<int:ingredient_pk>/toggle/', views.toggle_ingredient_completion, name='toggle_ingredient_completion'),
    path('<int:recipe_pk>/step/<int:step_pk>/toggle/', views.toggle_step_completion, name='toggle_step_completion'),
]
