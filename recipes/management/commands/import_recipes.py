# recipes/management/commands/import_recipes.py

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings # This import is correct
from recipes.models import Recipe, Ingredient, Step
from django.contrib.auth.models import User # Needed if you're creating dummy users for completion

class Command(BaseCommand):
    help = 'Imports recipes from a specified CSV file in the archives_csv directory.'

    def add_arguments(self, parser):
        parser.add_argument('csv_filename', type=str, help='The name of the CSV file to import (e.g., chilean_recipes.csv)')

    def handle(self, *args, **kwargs):
        csv_filename = kwargs['csv_filename']

        # Ensure CSV_ARCHIVES_DIR is defined in settings
        if not hasattr(settings, 'CSV_ARCHIVES_DIR'):
            raise CommandError("CSV_ARCHIVES_DIR is not defined in your settings.py file.")

        csv_filepath = os.path.join(settings.CSV_ARCHIVES_DIR, csv_filename)

        if not os.path.exists(csv_filepath):
            raise CommandError(f'CSV file "{csv_filepath}" does not exist at {csv_filepath}. Please check the path and filename.')

        self.stdout.write(self.style.SUCCESS(f'Attempting to import recipes from: {csv_filepath}'))

        try:
            with open(csv_filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    recipe_name = row.get('recipe name')
                    if not recipe_name:
                        self.stdout.write(self.style.WARNING(f"Skipping row due to missing 'recipe name': {row}"))
                        continue

                    # Clean and convert data
                    # Use .get() with a default to handle potentially missing columns gracefully
                    preparation_time_str = row.get('preparation time')
                    preparation_time = float(preparation_time_str) if preparation_time_str else None

                    min_portion_str = row.get('min_portion')
                    min_portion = int(min_portion_str) if min_portion_str else None

                    max_portion_str = row.get('max_portion')
                    max_portion = int(max_portion_str) if max_portion_str else None

                    # Create or get the Recipe
                    recipe, created = Recipe.objects.get_or_create(
                        name=recipe_name,
                        defaults={
                            'preparation_time': preparation_time,
                            'min_portion': min_portion,
                            'max_portion': max_portion
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created recipe: {recipe.name}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Recipe "{recipe.name}" already exists. Updating its details.'))
                        # Update existing recipe fields
                        recipe.preparation_time = preparation_time
                        recipe.min_portion = min_portion
                        recipe.max_portion = max_portion
                        recipe.save()


                    # Process Ingredients
                    # Ensure ingredients string is handled even if empty or malformed
                    ingredients_raw = row.get('ingredients', '[]')
                    if ingredients_raw:
                        # This parsing assumes the format "['item1', 'item2']"
                        # It removes brackets, splits by "', '", and then cleans each item
                        ingredients_list = [
                            item.strip().strip("'") for item in ingredients_raw.strip("[]").split("', '") if item.strip()
                        ]
                        for ing_name in ingredients_list:
                            if ing_name: # Ensure it's not an empty string after stripping
                                Ingredient.objects.get_or_create(recipe=recipe, name=ing_name)
                    else:
                        self.stdout.write(self.style.WARNING(f'No ingredients found for recipe: {recipe.name}'))


                    # Process Steps
                    # Ensure steps string is handled even if empty or malformed
                    steps_raw = row.get('steps', '[]')
                    if steps_raw:
                        # Similar parsing for steps
                        steps_list = [
                            item.strip().strip("'") for item in steps_raw.strip("[]").split("', '") if item.strip()
                        ]
                        for i, step_desc in enumerate(steps_list):
                            if step_desc: # Ensure it's not an empty string after stripping
                                Step.objects.get_or_create(recipe=recipe, order=i+1, description=step_desc)
                    else:
                        self.stdout.write(self.style.WARNING(f'No steps found for recipe: {recipe.name}'))

            self.stdout.write(self.style.SUCCESS('Successfully imported recipes from CSV.'))

        except FileNotFoundError:
            raise CommandError(f'CSV file "{csv_filepath}" not found.')
        except Exception as e:
            # Catch more specific errors if possible, but a general catch-all is good for debugging
            raise CommandError(f'Error during import for row {row.get("recipe name", "unknown")}: {e}')

