from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),  
    path('favorites/', views.favorite_list, name='favorite_list'),  
    path('recipe/<int:pk>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'), 
    path('recipe/<int:pk>/', views.recipe_detail, name='recipe_detail'),  
    path('<int:recipe_pk>/ingredient/<int:ingredient_pk>/toggle/', views.toggle_ingredient_completion, name='toggle_ingredient_completion'),  
    path('<int:recipe_pk>/step/<int:step_pk>/toggle/', views.toggle_step_completion, name='toggle_step_completion'), 

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),  
    path('admin/recipe/create/', views.admin_recipe_create, name='admin_recipe_create'), 
    path('admin/recipe/edit/<int:pk>/', views.recipe_edit, name='admin_recipe_edit'),  
    path('admin/recipe/delete/<int:pk>/', views.recipe_delete, name='admin_recipe_delete'),  
    path('admin/report/<int:id>/', views.generate_recipe_pdf, name='admin_generate_report'),  

    path('accounts/', include('django.contrib.auth.urls')),  
    path('accounts/register/', views.register, name='register'), 

    path('recipes/new/', views.recipe_create, name='recipe_create'),

    path('api/recipe_chat/', views.recipe_chat, name='recipe_chat'),

    path("enviar-receta/", views.enviar_receta, name="enviar_receta"),
    path("historial-json/", views.ver_historial, name="ver_historial_json"),
    path("recibir-json-pdf/", views.recibir_json_pdf, name="recibir_json_pdf"),
    path("json/<int:id>/", views.mostrar_json_pdf, name='mostrar_json_pdf'),
    path('json/<int:id>/pdf/', views.descargar_json_pdf, name='descargar_json_pdf'),
    path("recipes/<int:pk>/pdf/", views.recipe_pdf, name="recipe_pdf"),
   ]

