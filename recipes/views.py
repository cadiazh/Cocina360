from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, Ingredient, Step, UserIngredientCompletion, UserStepCompletion
from django.contrib.auth.models import User 
from django.contrib.auth import login
from .forms import RegisterForm, RecipeForm, IngredientFormSet, StepFormSet
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponseForbidden

def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})


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
