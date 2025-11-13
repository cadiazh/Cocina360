import os
import json
from openai import OpenAI

client = OpenAI()

def suggest_substitution(missing, substitute, recipe_title=None, recipe_text=None):
    """
    Llama al modelo GPT-5-nano para sugerir sustituciones culinarias.
    Devuelve un dict con:
    viable, explicacion, proporcion, ajustes, riesgos, confianza
    """

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

    response = client.responses.create(
        model="gpt-5-nano",
        input=prompt,
        response_format="json"
    )

    return json.loads(response.output_text)
