from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required # Comment out or remove this line
from .models import Recipe, Ingredient, Step, UserIngredientCompletion, UserStepCompletion
from django.contrib.auth.models import User # Import User model

def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, 'recipes/recipe_list.html', {'recipes': recipes})

# Temporarily remove @login_required for testing
# @login_required
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    # --- TEMPORARY LOGIC FOR TESTING WITHOUT LOGIN ---
    # If you're not logged in, we'll use a dummy user or the first user found
    # This is NOT for production, just for testing the UI
    if request.user.is_authenticated:
        current_user = request.user
    else:
        # For testing purposes, let's try to get the first user or create a dummy one
        # You MUST have at least one user in your database (e.g., a superuser)
        # for this to work without errors if no user is logged in.
        try:
            current_user = User.objects.first()
            if not current_user:
                # Fallback if no users exist at all (highly unlikely after createsuperuser)
                # This part is just to prevent crashes during testing
                current_user = User.objects.create_user(username='guest_tester', password='password123')
                print("Created a temporary guest_tester user for anonymous access.")
        except Exception as e:
            # Handle cases where User model might not be ready or other issues
            print(f"Could not get or create a user for anonymous access: {e}")
            # You might want to redirect or show an error page here in a real app
            return render(request, 'recipes/error.html', {'message': 'User context missing for anonymous access.'})
    # --- END TEMPORARY LOGIC ---

    # Get user's completion status for ingredients and steps
    ingredients_with_status = []
    for ingredient in recipe.ingredients.all():
        completion, created = UserIngredientCompletion.objects.get_or_create(
            user=current_user, ingredient=ingredient # Use current_user here
        )
        ingredients_with_status.append({
            'ingredient': ingredient,
            'completed': completion.completed
        })

    steps_with_status = []
    for step in recipe.steps.all():
        completion, created = UserStepCompletion.objects.get_or_create(
            user=current_user, step=step # Use current_user here
        )
        steps_with_status.append({
            'step': step,
            'completed': completion.completed
        })

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients_with_status': ingredients_with_status,
        'steps_with_status': steps_with_status,
        'user_is_authenticated': request.user.is_authenticated # Pass this to template for conditional display
    })

# Temporarily remove @login_required for testing
# @login_required
def toggle_ingredient_completion(request, recipe_pk, ingredient_pk):
    if request.method == 'POST':
        # --- TEMPORARY LOGIC FOR TESTING WITHOUT LOGIN ---
        if request.user.is_authenticated:
            current_user = request.user
        else:
            current_user = User.objects.first() # Assuming a user exists for testing
            if not current_user:
                # Handle if no user exists even for testing
                return redirect('recipe_list') # Or an error page
        # --- END TEMPORARY LOGIC ---

        ingredient = get_object_or_404(Ingredient, pk=ingredient_pk)
        completion, created = UserIngredientCompletion.objects.get_or_create(
            user=current_user, ingredient=ingredient # Use current_user here
        )
        completion.completed = not completion.completed
        completion.save()
    return redirect('recipe_detail', pk=recipe_pk)

# Temporarily remove @login_required for testing
# @login_required
def toggle_step_completion(request, recipe_pk, step_pk):
    if request.method == 'POST':
        # --- TEMPORARY LOGIC FOR TESTING WITHOUT LOGIN ---
        if request.user.is_authenticated:
            current_user = request.user
        else:
            current_user = User.objects.first() # Assuming a user exists for testing
            if not current_user:
                # Handle if no user exists even for testing
                return redirect('recipe_list') # Or an error page
        # --- END TEMPORARY LOGIC ---

        step = get_object_or_404(Step, pk=step_pk)
        completion, created = UserStepCompletion.objects.get_or_create(
            user=current_user, step=step # Use current_user here
        )
        completion.completed = not completion.completed
        completion.save()
    return redirect('recipe_detail', pk=recipe_pk)

