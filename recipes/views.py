from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, Ingredient, Step, UserIngredientCompletion, UserStepCompletion, FavoriteRecipe
from django.contrib.auth.models import User 
from django.contrib.auth import login, logout
from django.views.decorators.http import require_POST
from .forms import RegisterForm, RecipeForm, IngredientFormSet, StepFormSet
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponseForbidden
from django.db.models import Q

def recipe_list(request):
    # Obtener parámetros de búsqueda
    ingredient_query = request.GET.get('ingredient', '').strip()
    max_time = request.GET.get('max_time', '').strip()
    recipes = Recipe.objects.all()
    if ingredient_query:
        # Filtrar recetas que tengan ingredientes que contengan el texto buscado (case insensitive)
        recipes = recipes.filter(
            ingredients__name__icontains=ingredient_query
        ).distinct()
    if max_time:
        try:
            max_time_float = float(max_time)
            recipes = recipes.filter(preparation_time__lte=max_time_float)
        except ValueError:
            pass  # Ignorar si no es número válido
    return render(request, 'recipes/recipe_list.html', {
        'recipes': recipes,
        'ingredient_query': ingredient_query,
        'max_time': max_time,
    })


def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)


    if request.user.is_authenticated:
        current_user = request.user
    else:

        try:
            current_user = User.objects.first()
            if not current_user:

                current_user = User.objects.create_user(username='guest_tester', password='password123')
                print("Created a temporary guest_tester user for anonymous access.")
        except Exception as e:

            print(f"Could not get or create a user for anonymous access: {e}")
 
            return render(request, 'recipes/error.html', {'message': 'User context missing for anonymous access.'})



    ingredients_with_status = []
    for ingredient in recipe.ingredients.all():
        completion, created = UserIngredientCompletion.objects.get_or_create(
            user=current_user, ingredient=ingredient 
        )
        ingredients_with_status.append({
            'ingredient': ingredient,
            'completed': completion.completed
        })

    steps_with_status = []
    for step in recipe.steps.all():
        completion, created = UserStepCompletion.objects.get_or_create(
            user=current_user, step=step 
        )
        steps_with_status.append({
            'step': step,
            'completed': completion.completed
        })

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients_with_status': ingredients_with_status,
        'steps_with_status': steps_with_status,
        'user_is_authenticated': request.user.is_authenticated 
    })


def toggle_ingredient_completion(request, recipe_pk, ingredient_pk):
    if request.method == 'POST':

        if request.user.is_authenticated:
            current_user = request.user
        else:
            current_user = User.objects.first()
            if not current_user:
 
                return redirect('recipe_list') 


        ingredient = get_object_or_404(Ingredient, pk=ingredient_pk)
        completion, created = UserIngredientCompletion.objects.get_or_create(
            user=current_user, ingredient=ingredient 
        )
        completion.completed = not completion.completed
        completion.save()
    return redirect('recipe_detail', pk=recipe_pk)


def toggle_step_completion(request, recipe_pk, step_pk):
    if request.method == 'POST':
 
        if request.user.is_authenticated:
            current_user = request.user
        else:
            current_user = User.objects.first() 
            if not current_user:

                return redirect('recipe_list') 


        step = get_object_or_404(Step, pk=step_pk)
        completion, created = UserStepCompletion.objects.get_or_create(
            user=current_user, step=step
        )
        completion.completed = not completion.completed
        completion.save()
    return redirect('recipe_detail', pk=recipe_pk)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request, user)
            return redirect('recipe_list')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('recipe_list')  # o la url que quieras

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

@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.creator != request.user:
        return HttpResponseForbidden("You are not allowed to delete this recipe.")
    if request.method == 'POST':
        recipe.delete()
        return redirect('recipe_list')
    return render(request, 'recipes/recipe_confirm_delete.html', {'recipe': recipe})

@login_required
def favorite_list(request):
    favorites = FavoriteRecipe.objects.filter(user=request.user).select_related('recipe')
    return render(request, 'recipes/favorite_list.html', {'favorites': favorites})

@login_required
def toggle_favorite(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    favorite, created = FavoriteRecipe.objects.get_or_create(user=request.user, recipe=recipe)
    if not created:
        # Ya existía, eliminar para quitar favorito
        favorite.delete()
    return redirect('recipe_detail', pk=pk)
