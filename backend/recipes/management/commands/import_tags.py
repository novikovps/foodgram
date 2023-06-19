import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Tag

TAGS_FILE = (settings.BASE_DIR).joinpath(r"data/tags.csv")

FILES = {
    Tag: TAGS_FILE,
}


class Command(BaseCommand):
    def read_from_csv(self, model, datafile):
        with open(datafile, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            tag_list = [
                model(name=row[0], color=row[1], slug=row[2]) for row in reader
            ]
            try:
                model.objects.bulk_create(tag_list, batch_size=100)
                self.stdout.write(self.style.SUCCESS("Теги успешно добавлены"))
            except Exception as e:
                self.stderr.write(f"Ошибка при добавлении тегов: {e}")

    def handle(self, *args, **kwargs):
        for model, datafile in FILES.items():
            self.read_from_csv(model, datafile)
