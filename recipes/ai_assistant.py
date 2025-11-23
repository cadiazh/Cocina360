import os
import json
from openai import OpenAI, OpenAIError


def suggest_substitution(missing, substitute, recipe_title=None, recipe_text=None):
    """
    Llama al modelo GPT-5-nano para sugerir sustituciones culinarias.
    Si no hay API Key disponible, devuelve un JSON indicando indisponibilidad.
    """

    # 1. Verificar si la API Key existe
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "viable": "no disponible",
            "explicacion": "El servicio de IA no está disponible por el momento (API key no configurada).",
            "proporcion": "N/A",
            "ajustes": "N/A",
            "riesgos": "N/A",
            "confianza": 0.0
        }

    # 2. Crear cliente SOLO si hay API Key
    client = OpenAI(api_key=api_key)

    prompt = f"""
Eres un chef experto en sustituciones de ingredientes.

Usuario pregunta:
¿Puedo sustituir "{missing}" por "{substitute}" en la receta "{recipe_title or "sin título"}"?

Detalles de receta:
{recipe_text or "No se especifican más detalles."}

Responde SOLO un JSON válido con este formato EXACTO:

{{
  "viable": "si" | "no" | "depende",
  "explicacion": "texto en español",
  "proporcion": "formato de sustitución recomendado",
  "ajustes": "ajustes necesarios en sabor, textura o técnica",
  "riesgos": "posibles problemas",
  "confianza": 0.0
}}
"""

    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=prompt,
            response_format="json"
        )

        return json.loads(response.output_text)

    except OpenAIError as e:
        # 3. Si OpenAI falla (límite, servidor caído, etc.)
        return {
            "viable": "no disponible",
            "explicacion": f"El servicio de IA no está disponible por el momento. Error: {str(e)}",
            "proporcion": "N/A",
            "ajustes": "N/A",
            "riesgos": "N/A",
            "confianza": 0.0
        }
