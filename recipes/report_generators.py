from abc import ABC, abstractmethod
import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics


class RecipeReportGenerator(ABC):
    @abstractmethod
    def generate(self, recipe) -> bytes:
        pass


def wrap_text(text: str, max_width: float, c: canvas.Canvas,
              font_name: str = "Helvetica", font_size: int = 12):
    """
    Divide 'text' en varias líneas para que cada una
    no supere 'max_width' en puntos (según la fuente actual).
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = (current_line + " " + word).strip()
        test_width = pdfmetrics.stringWidth(test_line, font_name, font_size)

        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


class PdfRecipeReportGenerator(RecipeReportGenerator):
    def generate(self, recipe) -> bytes:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Configuración básica de la página
        width, height = letter
        left_margin = 50
        right_margin = 50
        usable_width = width - left_margin - right_margin

        y = height - 50  # 750 aprox. para carta

        # ----- TÍTULO -----
        p.setFont("Helvetica-Bold", 18)
        p.drawString(left_margin, y, recipe.name)
        y -= 30

        # ----- INFO BÁSICA -----
        p.setFont("Helvetica", 12)
        if getattr(recipe, "preparation_time", None):
            p.drawString(
                left_margin,
                y,
                f"Tiempo de preparación: {recipe.preparation_time} minutos",
            )
            y -= 20

        if getattr(recipe, "min_portion", None) or getattr(recipe, "max_portion", None):
            porciones = ""
            if getattr(recipe, "min_portion", None):
                porciones += str(recipe.min_portion)
            if getattr(recipe, "max_portion", None):
                porciones += f" - {recipe.max_portion}"
            p.drawString(left_margin, y, f"Porciones: {porciones}")
            y -= 30

        # ----- INGREDIENTES -----
        p.setFont("Helvetica-Bold", 14)
        p.drawString(left_margin, y, "Ingredientes:")
        y -= 20

        p.setFont("Helvetica", 12)
        for ing in recipe.ingredients.all():
            text = f"- {ing.name}"
            lines = wrap_text(text, usable_width, p, "Helvetica", 12)

            for line in lines:
                p.drawString(left_margin + 10, y, line)
                y -= 15

                if y < 50:
                    p.showPage()
                    y = height - 50
                    p.setFont("Helvetica", 12)  # re-aplicar fuente

        y -= 20

        # ----- PASOS -----
        p.setFont("Helvetica-Bold", 14)
        p.drawString(left_margin, y, "Pasos:")
        y -= 20

        p.setFont("Helvetica", 12)

        # Obtener queryset de pasos
        steps_qs = []
        if hasattr(recipe, "steps"):
            try:
                steps_qs = recipe.steps.all()
            except TypeError:
                steps_qs = []

        if not steps_qs and hasattr(recipe, "step_set"):
            steps_qs = recipe.step_set.all()

        if steps_qs:
            for idx, step in enumerate(steps_qs, start=1):
                text = None
                for field_name in (
                    "cleaned_description",
                    "description",
                    "text",
                    "instruction",
                    "content",
                ):
                    if hasattr(step, field_name):
                        text = getattr(step, field_name)
                        break

                if text is None:
                    text = str(step)

                full_text = f"{idx}. {text}"
                lines = wrap_text(full_text, usable_width, p, "Helvetica", 12)

                for line in lines:
                    p.drawString(left_margin + 10, y, line)
                    y -= 15

                    # Salto de página si no cabe
                    if y < 50:
                        p.showPage()
                        y = height - 50
                        p.setFont("Helvetica", 12)
        else:
            p.drawString(left_margin + 10, y, "Sin pasos registrados.")
            y -= 15

        # Cerrar página y PDF
        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()
        return pdf


class RecipeReportService:
    def __init__(self, generator: RecipeReportGenerator):
        self.generator = generator

    def build_report(self, recipe) -> bytes:
        return self.generator.generate(recipe)
