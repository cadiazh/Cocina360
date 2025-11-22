import os
import json
import openai
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la clave de la API de OpenAI desde las variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    # Realizar la consulta a OpenAI
    try:
        response = openai.Completion.create(
            model="text-davinci-003",  
            prompt=prompt,
            max_tokens=500, 
            temperature=0.7
        )

        response_text = response.choices[0].text.strip()
        return json.loads(response_text)

    except Exception as e:
        print(f"Error al llamar a la API de OpenAI: {e}")
        return None
