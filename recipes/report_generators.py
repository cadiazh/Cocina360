from abc import ABC, abstractmethod
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class RecipeReportGenerator(ABC):
    @abstractmethod
    def generate(self, recipe) -> bytes:
        pass


class PdfRecipeReportGenerator(RecipeReportGenerator):
    def generate(self, recipe) -> bytes:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        y = 750

        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, y, recipe.name)
        y -= 30

        p.setFont("Helvetica", 12)
        if getattr(recipe, "preparation_time", None):
            p.drawString(50, y, f"Tiempo de preparación: {recipe.preparation_time} minutos")
            y -= 20

        if getattr(recipe, "min_portion", None) or getattr(recipe, "max_portion", None):
            porciones = ""
            if getattr(recipe, "min_portion", None):
                porciones += str(recipe.min_portion)
            if getattr(recipe, "max_portion", None):
                porciones += f" - {recipe.max_portion}"
            p.drawString(50, y, f"Porciones: {porciones}")
            y -= 30

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Ingredientes:")
        y -= 20

        p.setFont("Helvetica", 12)
        for ing in recipe.ingredients.all():
            p.drawString(60, y, f"- {ing.name}")
            y -= 15
            if y < 50:
                p.showPage()
                y = 750

        y -= 20

        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Pasos:")
        y -= 20

        p.setFont("Helvetica", 12)

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
                for field_name in ("cleaned_description", "description", "text", "instruction", "content"):
                    if hasattr(step, field_name):
                        text = getattr(step, field_name)
                        break
                if text is None:
                    text = str(step)

                line = f"{idx}. {text}"
                p.drawString(60, y, line)
                y -= 15

                if y < 50:
                    p.showPage()
                    y = 750
        else:
            p.drawString(60, y, "Sin pasos registrados.")

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
