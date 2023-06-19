import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

INGREDIENTS_FILE = (settings.BASE_DIR).joinpath(r"data/ingredients.csv")

FILES = {
    Ingredient: INGREDIENTS_FILE,
}


class Command(BaseCommand):
    def read_from_csv(self, model, datafile):
        with open(datafile, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            ingredient_list = [
                model(name=row[0], measurement_unit=row[1]) for row in reader
            ]
            try:
                model.objects.bulk_create(ingredient_list, batch_size=100)
                self.stdout.write(
                    self.style.SUCCESS("Ингедиенты успешно добавлены")
                )
            except Exception as e:
                self.stderr.write(f"Ошибка при добавлении рецептов: {e}")

    def handle(self, *args, **kwargs):
        for model, datafile in FILES.items():
            self.read_from_csv(model, datafile)
