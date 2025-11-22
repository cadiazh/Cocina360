from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, Ingredient, Step, UserIngredientCompletion, UserStepCompletion, FavoriteRecipe
from django.contrib.auth.models import User 
from django.contrib.auth import login, logout
from django.views.decorators.http import require_POST
from .forms import RegisterForm, RecipeForm, IngredientFormSet, StepFormSet
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Recipe, Ingredient, Step
from .forms import RecipeForm
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt  
import json  
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.template.loader import render_to_string

# List of Recipes
def recipe_list(request):
    ingredient_query = request.GET.get('ingredient', '').strip()
    max_time = request.GET.get('max_time', '').strip()
    recipes = Recipe.objects.all()
    
    if ingredient_query:
        recipes = recipes.filter(ingredients__name__icontains=ingredient_query).distinct()
    
    if max_time:
        try:
            max_time_float = float(max_time)
            recipes = recipes.filter(preparation_time__lte=max_time_float)
        except ValueError:
            pass  # Ignore if not a valid number
    
    return render(request, 'recipes/recipe_list.html', {
        'recipes': recipes,
        'ingredient_query': ingredient_query,
        'max_time': max_time,
    })

# Recipe Details
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    if request.user.is_authenticated:
        current_user = request.user
    else:
        try:
            current_user = User.objects.first()
            if not current_user:
                current_user = User.objects.create_user(username='guest_tester', password='password123')
        except Exception as e:
            print(f"Error: {e}")
            return render(request, 'recipes/error.html', {'message': 'User context missing for anonymous access.'})

    # Handling Ingredients and Steps with Status
    ingredients_with_status = []
    for ingredient in recipe.ingredients.all():
        completion, created = UserIngredientCompletion.objects.get_or_create(user=current_user, ingredient=ingredient)
        ingredients_with_status.append({'ingredient': ingredient, 'completed': completion.completed})

    steps_with_status = []
    for step in recipe.steps.all():
        completion, created = UserStepCompletion.objects.get_or_create(user=current_user, step=step)
        steps_with_status.append({'step': step, 'completed': completion.completed})

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients_with_status': ingredients_with_status,
        'steps_with_status': steps_with_status,
        'user_is_authenticated': request.user.is_authenticated
    })

# Toggle Ingredient Completion
def toggle_ingredient_completion(request, recipe_pk, ingredient_pk):
    if request.method == 'POST':
        current_user = request.user if request.user.is_authenticated else User.objects.first()
        ingredient = get_object_or_404(Ingredient, pk=ingredient_pk)
        completion, created = UserIngredientCompletion.objects.get_or_create(user=current_user, ingredient=ingredient)
        completion.completed = not completion.completed
        completion.save()
    return redirect('recipe_detail', pk=recipe_pk)

# Toggle Step Completion
def toggle_step_completion(request, recipe_pk, step_pk):
    if request.method == 'POST':
        current_user = request.user if request.user.is_authenticated else User.objects.first()
        step = get_object_or_404(Step, pk=step_pk)
        completion, created = UserStepCompletion.objects.get_or_create(user=current_user, step=step)
        completion.completed = not completion.completed
        completion.save()
    return redirect('recipe_detail', pk=recipe_pk)

# User Registration
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, user)
            return redirect('recipe_list')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

# Logout view
@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('recipe_list')

# Create Recipe
@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        ingredient_formset = IngredientFormSet(request.POST)
        step_formset = StepFormSet(request.POST)
        if form.is_valid() and ingredient_formset.is_valid() and step_formset.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user
            recipe.save()
            ingredient_formset.instance = recipe
            ingredient_formset.save()
            step_formset.instance = recipe
            step_formset.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
        ingredient_formset = IngredientFormSet()
        step_formset = StepFormSet()
    return render(request, 'recipes/recipe_form.html', {
        'form': form,
        'ingredient_formset': ingredient_formset,
        'step_formset': step_formset,
    })

# Delete Recipe
@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.creator != request.user:
        return HttpResponseForbidden("You are not allowed to delete this recipe.")
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'recipes/recipe_confirm_delete.html', {'recipe': recipe})

# Favorite Recipes
@login_required
def favorite_list(request):
    favorites = FavoriteRecipe.objects.filter(user=request.user).select_related('recipe')
    return render(request, 'recipes/favorite_list.html', {'favorites': favorites})

# Toggle Favorite
@login_required
def toggle_favorite(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    favorite, created = FavoriteRecipe.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        favorite.delete()
    return redirect('recipe_detail', pk=pk)

# Admin - Check if the user is an admin
def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    recipes = Recipe.objects.all()
    ingredients = Ingredient.objects.all()
    steps = Step.objects.all()
    return render(request, 'recipes/admin_dashboard.html', {
        'recipes': recipes,
        'ingredients': ingredients,
        'steps': steps,
    })

# Create Recipe for Admin
@user_passes_test(is_admin)
def admin_recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.creator = request.user
            recipe.save()
            messages.success(request, "Recipe created successfully.")
            return redirect('admin_dashboard')
    else:
        form = RecipeForm()

    return render(request, 'recipes/recipe_form.html', {'form': form})

# Edit Recipe for Admin
@user_passes_test(is_admin)
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.creator != request.user:
        messages.error(request, "You don't have permission to edit this recipe.")
        return redirect('recipe_list')

    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, "Recipe edited successfully.")
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'recipes/recipe_form.html', {'form': form})

# Delete Recipe for Admin
@user_passes_test(is_admin)
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, "Recipe deleted successfully.")
        return redirect('recipe_list')
    return render(request, 'recipes/recipe_confirm_delete.html', {'recipe': recipe})

# Generate Recipe PDF
def generate_recipe_pdf(request, id):
    # Obtener la receta por id
    recipe = Recipe.objects.get(id=id)
    
    # Crear un archivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{recipe.name}_recipe.pdf"'

    # Crear el canvas de reporte
    p = canvas.Canvas(response, pagesize=letter)
    
    # Añadir texto al PDF
    p.drawString(100, 750, f"Receta: {recipe.name}")
    p.drawString(100, 730, "Ingredientes:")
    
    # Mostrar los ingredientes
    y_position = 710
    for ingredient in recipe.ingredients.all():
        p.drawString(100, y_position, f"- {ingredient.name}")
        y_position -= 20  # Baja para el siguiente ingrediente
    
    p.drawString(100, y_position - 20, "Instrucciones:")
    
    # Mostrar los pasos de la receta
    y_position -= 40
    for step in recipe.steps.all():
        p.drawString(100, y_position, f"{step.order}. {step.description}")
        y_position -= 20
    
    p.showPage()  # Finaliza la página
    p.save()  # Guarda el PDF

    return response

# En recipes/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import openai  # Si estás utilizando OpenAI para interactuar con la IA

openai.api_key = 'tu-clave-api'  # Agrega tu clave API aquí

@csrf_exempt  # Permite solicitudes POST sin token CSRF
def recipe_chat(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')  # Obtener el mensaje del usuario

        try:
            # Interactuar con la API de IA (aquí OpenAI como ejemplo)
            response = openai.Completion.create(
                engine="text-davinci-003",  # Puedes usar el modelo que prefieras
                prompt=f"Responde con una receta o consejos basados en: {user_message}",
                max_tokens=150
            )

            # Devolver la respuesta de la IA
            return JsonResponse({"response": response.choices[0].text.strip()})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Invalid method"}, status=405)

from django.contrib.admin.views.decorators import staff_member_required
@staff_member_required  
def admin_dashboard(request):
    
    return render(request, 'admin/dashboard.html') 