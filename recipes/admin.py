from django.contrib import admin
from .models import Recipe, Ingredient, Step, UserIngredientCompletion, UserStepCompletion

class IngredientInline(admin.TabularInline):
    model = Ingredient
    extra = 1

class StepInline(admin.TabularInline):
    model = Step
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'preparation_time', 'min_portion', 'max_portion')
    inlines = [IngredientInline, StepInline]

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'recipe')
    list_filter = ('recipe',)

@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ('order', 'description', 'recipe')
    list_filter = ('recipe',)

@admin.register(UserIngredientCompletion)
class UserIngredientCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingredient', 'completed')
    list_filter = ('user', 'completed')

@admin.register(UserStepCompletion)
class UserStepCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'step', 'completed')
    list_filter = ('user', 'completed')
