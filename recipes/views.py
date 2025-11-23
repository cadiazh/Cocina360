from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, Ingredient, Step, UserIngredientCompletion, UserStepCompletion, FavoriteRecipe
from django.contrib.auth.models import User 
from django.contrib.auth import login, logout
from django.views.decorators.http import require_POST
from .forms import RegisterForm, RecipeForm, IngredientFormSet, StepFormSet
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseBadRequest, FileResponse, HttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Recipe, Ingredient, Step, JsonHistory 
from openai import OpenAI
from .ai_assistant import suggest_substitution
from .forms import RecipeForm
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt  
import os, io, random, requests, json, re 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from xhtml2pdf import pisa
from django.conf import settings
from io import BytesIO
from django.template.loader import render_to_string

def recipe_list(request):
    query = request.GET.get("q", "")  # lo que viene del buscador superior
    ingredient_query = request.GET.get("ingredient", "")
    max_time = request.GET.get("max_time", "")

    recipes = Recipe.objects.all()

    # BUSCAR POR NOMBRE
    if query:
        recipes = recipes.filter(name__icontains=query)

    # Filtrar por ingrediente
    if ingredient_query:
        recipes = recipes.filter(ingredients__name__icontains=ingredient_query)

    # Filtrar por tiempo
    if max_time:
        recipes = recipes.filter(preparation_time__lte=max_time)

    recipes = recipes.distinct()

    return render(request, "recipes/recipe_list.html", {
        "recipes": recipes,
        "ingredient_query": ingredient_query,
        "max_time": max_time,
        "query": query,
    })

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    # Usuario autenticado o fallback temporal
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

    # --------------------------
    # INGREDIENTES COMPLETADOS
    # --------------------------
    ingredients_with_status = []
    for ingredient in recipe.ingredients.all():
        completion, created = UserIngredientCompletion.objects.get_or_create(
            user=current_user, ingredient=ingredient
        )
        ingredients_with_status.append({
            'ingredient': ingredient,
            'completed': completion.completed
        })

    # --------------------------
    # PASOS COMPLETADOS + LIMPIEZA DE "1-" "2-" etc.
    # --------------------------
    steps_with_status = []
    for step in recipe.steps.all():
        completion, created = UserStepCompletion.objects.get_or_create(
            user=current_user, step=step
        )

        # --- MODIFICACIÓN CLAVE ---
        # Elimina el patrón "X-" al inicio de la descripción
        cleaned_description = re.sub(r'^\d+-\s*', '', step.description)

        steps_with_status.append({
            'step': step,
            'completed': completion.completed,
            'cleaned_description': cleaned_description
        })

    # --------------------------
    # FAVORITOS PARA PINTAR EL CORAZÓN
    # --------------------------
    if request.user.is_authenticated:
        favorite_recipe_ids = FavoriteRecipe.objects.filter(
            user=request.user
        ).values_list('recipe__pk', flat=True)
    else:
        favorite_recipe_ids = []

    # --------------------------
    # RENDER
    # --------------------------
    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'ingredients_with_status': ingredients_with_status,
        'steps_with_status': steps_with_status,
        'user_is_authenticated': request.user.is_authenticated,
        'favorite_recipe_ids': favorite_recipe_ids,
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

# Crear cliente solo si existe la API key
api_key = os.environ.get("OPENAI_API_KEY", None)

client = None
if api_key:
    client = OpenAI(api_key=api_key)

@csrf_exempt
@require_POST
def recipe_chat(request):
    """
    Chat general sobre la receta actual.

    Espera JSON:
      { "message": "texto del usuario", "recipe_id": 1 }

    Responde JSON:
      { "reply": "texto de la IA" }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido")

    message = data.get("message")
    recipe_id = data.get("recipe_id")

    if not message or not recipe_id:
        return HttpResponseBadRequest("Faltan 'message' o 'recipe_id'")

    recipe = get_object_or_404(Recipe, pk=recipe_id)

    ingredientes_txt = ", ".join(
        ing.name for ing in recipe.ingredients.all()
    )
    pasos_txt = "\n".join(
        f"{i+1}. {step.description}"
        for i, step in enumerate(recipe.steps.all())
    )

    prompt = f"""
Eres un asistente de cocina amable y experto.
El usuario está viendo esta receta de Cocina360 y te hará preguntas sobre ella.

Receta:
Nombre: {recipe.name}
Ingredientes: {ingredientes_txt}
Pasos:
{pasos_txt}

Reglas:
- Responde SIEMPRE en español.
- Sé breve y claro (3–6 líneas).
- Puedes dar consejos adicionales (textura, sabor, tiempos, seguridad).
- Si el usuario pide sustituir algo, explica riesgos y proporciones.
- Si la pregunta no tiene que ver con la receta, responde de forma educada pero vuelve al tema de la receta.

Pregunta del usuario: {message}
Responde de forma directa, como si estuvieras hablando con la persona.
"""

        # Si no hay cliente, usa modo sin IA
    if client is None:
        reply_text = (
            "⚠️ Modo sin IA activado.\n"
            "No hay API key configurada, por lo que responderé con mensajes básicos.\n\n"
            f"Pregunta: {message}\n"
            "Respuesta: Esta es una respuesta simulada. La integración con la IA está desactivada."
        )
    else:
        try:
            response = client.responses.create(
                model="gpt-5-nano",
                input=prompt,
                store=False
            )
            reply_text = response.output_text
        except Exception as e:
            reply_text = (
                "⚠️ Error consultando la IA.\n"
                "Por ahora usaré el modo sin IA.\n"
                f"Detalle: {e}"
            )


    return JsonResponse({"reply": reply_text})  

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required  
def admin_dashboard(request):
    
    return render(request, 'admin/dashboard.html') 

@csrf_exempt
def recibir_json_pdf(request):
    """
    Recibe un JSON y genera un PDF automáticamente.
    También lo almacena en historial (máximo 10).
    """

    if request.method != "POST":
        return HttpResponseBadRequest("Solo se acepta POST con JSON.")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("JSON inválido.")

    # Guardar JSON en historial
    entry = JsonHistory.objects.create(content=data)

    # Mantener solo los 10 más recientes
    ids_keep = JsonHistory.objects.order_by("-timestamp")[:10].values_list("id", flat=True)
    JsonHistory.objects.exclude(id__in=ids_keep).delete()

    # Crear PDF en memoria
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    p.setFont("Helvetica", 12)

    p.drawString(50, 780, "Reporte JSON recibido")

    for key, value in data.items():
        p.drawString(50, y, f"{key}: {value}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)

    # Devolver PDF descargable
    return FileResponse(buffer, as_attachment=True, filename="json_recibido.pdf")


def ver_historial(request):
    """
    Muestra los últimos 10 JSON almacenados.
    """
    historial = JsonHistory.objects.all()[:10]
    return JsonResponse({
        "cantidad": len(historial),
        "data": [h.content for h in historial]
    })





def enviar_receta(request):

    if request.method == "GET":
        return render(request, "equipo_precedente/enviar_receta.html")

    if request.method == "POST":
        destino = request.POST.get("destino")

        if not destino:
            return HttpResponseBadRequest("Debes ingresar una URL destino.")

        # Obtener receta aleatoria
        recetas = Recipe.objects.all()
        if not recetas.exists():
            return JsonResponse({"error": "No hay recetas en la base de datos."})

        receta = random.choice(list(recetas))

        payload = {
            "id": receta.id,
            "nombre": receta.name,
            "ingredientes": [i.name for i in receta.ingredients.all()],
            "pasos": [s.description for s in receta.steps.all()],
        }

        try:
            resp = requests.post(destino, json=payload, timeout=5)
            return JsonResponse({
                "mensaje": "JSON enviado correctamente",
                "destino": destino,
                "respuesta_del_servidor": resp.text
            })
        except Exception as e:
            return JsonResponse({"error": f"No se pudo enviar: {str(e)}"})



@csrf_exempt
def recibir_json_pdf(request):
    # GET --> mostrar la página de espera (waiting_json.html)
    if request.method == "GET":
        # Aseguramos que la página de espera no reciba datos temporales.
        return render(request, "equipo_precedente/waiting_json.html", {})

    # POST --> Viene un JSON enviado por otro servidor
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        # Respuesta JSON de error si el JSON es inválido.
        return HttpResponseBadRequest(
            json.dumps({"status": "ERROR", "mensaje": "JSON inválido."}),
            content_type="application/json"
        )

    # Guardar el JSON en la base de datos
    entry = JsonHistory.objects.create(content=data)

    # Obtener el link de visualización
    # Usamos reverse y request.build_absolute_uri para obtener el link completo
    view_link = request.build_absolute_uri(reverse("mostrar_json_pdf", args=[entry.id]))

    # Mantener historial máximo 10
    ids_keep = JsonHistory.objects.order_by("-timestamp")[:10].values_list("id", flat=True)
    JsonHistory.objects.exclude(id__in=ids_keep).delete()

    # Respuesta al otro servidor: CONCISA Y EN JSON
    return JsonResponse({
        "status": "recibido correctamente", 
        "id": entry.id,
        "link_ver_recepcion": view_link,
    })


# Vista para mostrar el JSON específico
def mostrar_json_pdf(request, id):
    json_entry = get_object_or_404(JsonHistory, id=id)
    json_pretty = json.dumps(json_entry.content, indent=4)

    return render(request, "equipo_precedente/mostrar_json_recibido.html", {
        "json_data": json_pretty,
        "id": json_entry.id,
    })

def render_to_pdf(template_src, context_dict={}):
    """Convierte una plantilla HTML y contexto a un archivo PDF."""
    html = render_to_string(template_src, context_dict)
    result = BytesIO()
    
    # Esta función transforma el HTML en PDF y escribe el resultado en 'result'
    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")), # El contenido HTML debe estar en Bytes
        result,
        link_callback=lambda uri, rel: settings.STATIC_ROOT # Callback para manejar rutas estáticas
    )
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    
    # Si hay un error en la generación, se devuelve un error de HTTP
    return HttpResponse('Tuvimos algunos errores al generar el PDF: %s' % html, status=500)


# La vista que llama a la función de ayuda
def descargar_json_pdf(request, id):
    # 1. Obtener el objeto JsonHistory
    json_entry = get_object_or_404(JsonHistory, id=id)

    # 2. Formatear el JSON para la plantilla
    json_pretty = json.dumps(json_entry.content, indent=4)
    
    context = {
        "json_data": json_pretty,
        "id": json_entry.id,
        "title": f"JSON Recibido #{json_entry.id}",
    }

    # 3. Generar el PDF
    pdf_response = render_to_pdf("equipo_precedente/pdf_json_template.html", context)
    
    # 4. Configurar la descarga del archivo
    if pdf_response.status_code == 200:
        pdf_response["Content-Disposition"] = f'attachment; filename="json_historial_{id}.pdf"'
    
    return pdf_response